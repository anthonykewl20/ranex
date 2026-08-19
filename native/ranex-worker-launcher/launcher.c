#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <linux/audit.h>
#include <linux/filter.h>
#include <linux/keyctl.h>
#include <linux/landlock.h>
#include <linux/seccomp.h>
#include <limits.h>
#include <stddef.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/prctl.h>
#include <sys/mount.h>
#include <sys/wait.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <sys/types.h>
#include <sched.h>
#include <unistd.h>

#define REQUEST_LIMIT 4096U
#define RESPONSE_LIMIT 65536U
#define REQUIRED_LANDLOCK_ABI 6
#define STAGE_TWO "--ranex-internal-stage-two"
#define WORKER_EXEC "--ranex-worker-exec"
#define WORKER_STATUS_FD "--ranex-status-fd="
#define WORKER_READY_ACK_FD "--ranex-ready-ack-fd="
#define WORKER_STATUS_DESCRIPTOR 4
#define WORKER_READY_PREFIX "ranex-worker-ready-v1 pid="
#define WORKER_READY_SUFFIX " nnp=1 landlock=1 seccomp=1 namespaces=user,mount,pid,ipc,network,cgroup\n"
#define CLOSED_FD_LIMIT 256U
#define ENVIRONMENT_LIMIT 64U
#define ENVIRONMENT_NAME_LIMIT 128U
#define INJECTED_SECRET_NAME "RANEX_SLICE017_INJECTED_SECRET"

struct probe_request {
    char environment_names[ENVIRONMENT_LIMIT][ENVIRONMENT_NAME_LIMIT];
    size_t environment_count;
};

struct stage_metadata {
    int closed[CLOSED_FD_LIMIT];
    size_t closed_count;
    long session_keyring_before;
};

/* Build hosts may carry pre-ABI-5 Landlock headers while the qualified kernel
 * exposes ABI 6.  Keep the ABI-6 UAPI layout and bit assignments explicit. */
struct ranex_landlock_ruleset_attr {
    __u64 handled_access_fs;
    __u64 handled_access_net;
    __u64 scoped;
};

#ifndef LANDLOCK_ACCESS_FS_IOCTL_DEV
#define LANDLOCK_ACCESS_FS_IOCTL_DEV (1ULL << 15)
#endif
#ifndef LANDLOCK_SCOPE_ABSTRACT_UNIX_SOCKET
#define LANDLOCK_SCOPE_ABSTRACT_UNIX_SOCKET (1ULL << 0)
#endif
#ifndef LANDLOCK_SCOPE_SIGNAL
#define LANDLOCK_SCOPE_SIGNAL (1ULL << 1)
#endif

/* Landlock ABI v1 filesystem rights, plus rights introduced by later ABIs. */
#define LANDLOCK_ACCESS_FS_V1                                                   \
    (LANDLOCK_ACCESS_FS_EXECUTE | LANDLOCK_ACCESS_FS_WRITE_FILE |              \
     LANDLOCK_ACCESS_FS_READ_FILE | LANDLOCK_ACCESS_FS_READ_DIR |              \
     LANDLOCK_ACCESS_FS_REMOVE_DIR | LANDLOCK_ACCESS_FS_REMOVE_FILE |          \
     LANDLOCK_ACCESS_FS_MAKE_CHAR | LANDLOCK_ACCESS_FS_MAKE_DIR |              \
     LANDLOCK_ACCESS_FS_MAKE_REG | LANDLOCK_ACCESS_FS_MAKE_SOCK |              \
     LANDLOCK_ACCESS_FS_MAKE_FIFO | LANDLOCK_ACCESS_FS_MAKE_BLOCK |            \
     LANDLOCK_ACCESS_FS_MAKE_SYM)

static __u64 landlock_fs_mask(long abi) {
    __u64 mask = LANDLOCK_ACCESS_FS_V1;
    if (abi >= 2) {
        mask |= LANDLOCK_ACCESS_FS_REFER;
    }
    if (abi >= 3) {
        mask |= LANDLOCK_ACCESS_FS_TRUNCATE;
    }
    if (abi >= 5) {
        mask |= LANDLOCK_ACCESS_FS_IOCTL_DEV;
    }
#ifdef LANDLOCK_ACCESS_FS_RESOLVE_UNIX
    if (abi >= 9) {
        mask |= LANDLOCK_ACCESS_FS_RESOLVE_UNIX;
    }
#endif
    return mask;
}

static int add_path_rule(int ruleset_fd, int parent_fd, __u64 allowed_access) {
    struct landlock_path_beneath_attr rule = {
        .allowed_access = allowed_access,
        .parent_fd = parent_fd,
    };
    return (int)syscall(SYS_landlock_add_rule, ruleset_fd,
                        LANDLOCK_RULE_PATH_BENEATH, &rule, 0U);
}

static int add_runtime_loader_rule(int ruleset_fd, const char *path, __u64 allowed_access) {
    struct stat facts;
    char *resolved = realpath(path, NULL);
    int descriptor;
    int result;

    if (resolved == NULL) {
        return -1;
    }
    descriptor = open(resolved, O_PATH | O_NOFOLLOW | O_CLOEXEC);
    free(resolved);
    if (descriptor < 0 || fstat(descriptor, &facts) != 0 || !S_ISREG(facts.st_mode) ||
        (facts.st_mode & (S_IWGRP | S_IWOTH)) != 0) {
        (void)close(descriptor);
        return -1;
    }
    result = add_path_rule(ruleset_fd, descriptor, allowed_access);
    (void)close(descriptor);
    return result;
}

static bool enforce_landlock(int executable_fd, int subject_fd, int toolchain_fd,
                             int output_fd, int scratch_fd) {
    struct ranex_landlock_ruleset_attr ruleset = {0};
    struct stat executable_facts;
    struct stat directory_facts;
    long abi;
    int ruleset_fd;
    __u64 filesystem_mask;
    __u64 executable_access;
    const __u64 readonly_access = LANDLOCK_ACCESS_FS_EXECUTE |
                                  LANDLOCK_ACCESS_FS_READ_FILE |
                                  LANDLOCK_ACCESS_FS_READ_DIR;

    abi = syscall(SYS_landlock_create_ruleset, NULL, 0U,
                  LANDLOCK_CREATE_RULESET_VERSION);
    if (abi < REQUIRED_LANDLOCK_ABI ||
        fstat(executable_fd, &executable_facts) != 0 ||
        fstat(subject_fd, &directory_facts) != 0 ||
        !S_ISDIR(directory_facts.st_mode) ||
        fstat(toolchain_fd, &directory_facts) != 0 ||
        !S_ISDIR(directory_facts.st_mode) ||
        fstat(output_fd, &directory_facts) != 0 ||
        !S_ISDIR(directory_facts.st_mode) ||
        fstat(scratch_fd, &directory_facts) != 0 ||
        !S_ISDIR(directory_facts.st_mode) ||
        !S_ISREG(executable_facts.st_mode)) {
        return false;
    }

    filesystem_mask = landlock_fs_mask(abi);
    ruleset.handled_access_fs = filesystem_mask;
    if (abi >= 4) {
        ruleset.handled_access_net =
            LANDLOCK_ACCESS_NET_BIND_TCP | LANDLOCK_ACCESS_NET_CONNECT_TCP;
    }
    if (abi >= 6) {
        ruleset.scoped = LANDLOCK_SCOPE_ABSTRACT_UNIX_SOCKET |
                          LANDLOCK_SCOPE_SIGNAL;
    }
    ruleset_fd = (int)syscall(SYS_landlock_create_ruleset, &ruleset,
                              sizeof(ruleset), 0U);
    if (ruleset_fd < 0) {
        return false;
    }

    /* Subject and toolchain are executable read-only trees.  The two declared
     * writable trees intentionally each receive the complete handled mask. */
    executable_access = LANDLOCK_ACCESS_FS_EXECUTE | LANDLOCK_ACCESS_FS_READ_FILE;
    if (add_path_rule(ruleset_fd, executable_fd, executable_access) != 0 ||
        /* The pinned x86-64 ELF ABI needs its interpreter and libc before the
         * command can enter its declared toolchain.  Both are exact trusted,
         * read-only runtime objects; no directory or writable host authority
         * is admitted. */
        add_runtime_loader_rule(ruleset_fd, "/lib64/ld-linux-x86-64.so.2",
                                executable_access) != 0 ||
        add_runtime_loader_rule(ruleset_fd, "/lib/x86_64-linux-gnu/libc.so.6",
                                LANDLOCK_ACCESS_FS_READ_FILE) != 0 ||
        add_path_rule(ruleset_fd, subject_fd, readonly_access) != 0 ||
        add_path_rule(ruleset_fd, toolchain_fd, readonly_access) != 0 ||
        add_path_rule(ruleset_fd, output_fd, filesystem_mask) != 0 ||
        add_path_rule(ruleset_fd, scratch_fd, filesystem_mask) != 0 ||
        syscall(SYS_landlock_restrict_self, ruleset_fd, 0U) != 0 ||
        close(ruleset_fd) != 0) {
        (void)close(ruleset_fd);
        return false;
    }
    return true;
}

/* The profile is x86-64-only: reject a mismatched audit architecture first. */
#define ALLOW_SYSCALL(number)                                                   \
    BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, (number), 0, 1),                        \
    BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW)

static bool enforce_seccomp(void) {
    static const struct sock_filter filter[] = {
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS,
                 offsetof(struct seccomp_data, arch)),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, AUDIT_ARCH_X86_64, 1, 0),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS),
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS,
                 offsetof(struct seccomp_data, nr)),
        /* Minimal static-worker and libc process-startup surface. */
        ALLOW_SYSCALL(__NR_read),
        ALLOW_SYSCALL(__NR_pread64),
        ALLOW_SYSCALL(__NR_write),
        ALLOW_SYSCALL(__NR_dup),
        ALLOW_SYSCALL(__NR_dup2),
        ALLOW_SYSCALL(__NR_dup3),
        ALLOW_SYSCALL(__NR_fcntl),
        ALLOW_SYSCALL(__NR_close),
        ALLOW_SYSCALL(__NR_openat),
        ALLOW_SYSCALL(__NR_newfstatat),
        ALLOW_SYSCALL(__NR_fstat),
        ALLOW_SYSCALL(__NR_lseek),
        ALLOW_SYSCALL(__NR_getdents64),
        ALLOW_SYSCALL(__NR_mmap),
        ALLOW_SYSCALL(__NR_mprotect),
        ALLOW_SYSCALL(__NR_munmap),
        ALLOW_SYSCALL(__NR_brk),
        ALLOW_SYSCALL(__NR_madvise),
        ALLOW_SYSCALL(__NR_rt_sigaction),
        ALLOW_SYSCALL(__NR_rt_sigprocmask),
        ALLOW_SYSCALL(__NR_rt_sigreturn),
        ALLOW_SYSCALL(__NR_arch_prctl),
        ALLOW_SYSCALL(__NR_set_tid_address),
        ALLOW_SYSCALL(__NR_set_robust_list),
        ALLOW_SYSCALL(__NR_rseq),
        ALLOW_SYSCALL(__NR_prlimit64),
        ALLOW_SYSCALL(__NR_clock_gettime),
        ALLOW_SYSCALL(__NR_clock_nanosleep),
        ALLOW_SYSCALL(__NR_getpid),
        ALLOW_SYSCALL(__NR_gettid),
        ALLOW_SYSCALL(__NR_getuid),
        ALLOW_SYSCALL(__NR_getgid),
        ALLOW_SYSCALL(__NR_geteuid),
        ALLOW_SYSCALL(__NR_getegid),
        ALLOW_SYSCALL(__NR_getppid),
        ALLOW_SYSCALL(__NR_getrandom),
        ALLOW_SYSCALL(__NR_futex),
        ALLOW_SYSCALL(__NR_sched_yield),
        ALLOW_SYSCALL(__NR_clone),
        ALLOW_SYSCALL(__NR_execve),
        ALLOW_SYSCALL(__NR_execveat),
        ALLOW_SYSCALL(__NR_wait4),
        ALLOW_SYSCALL(__NR_exit),
        ALLOW_SYSCALL(__NR_exit_group),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ERRNO | (EPERM & SECCOMP_RET_DATA)),
    };
    const struct sock_fprog program = {
        .len = (unsigned short)(sizeof(filter) / sizeof(filter[0])),
        .filter = (struct sock_filter *)filter,
    };
    return syscall(SYS_seccomp, SECCOMP_SET_MODE_FILTER, 0U, &program) == 0;
}

static int write_all(int descriptor, const char *buffer, size_t length) {
    while (length != 0U) {
        ssize_t written = write(descriptor, buffer, length);
        if (written < 0 && errno == EINTR) {
            continue;
        }
        if (written <= 0) {
            return -1;
        }
        buffer += (size_t)written;
        length -= (size_t)written;
    }
    return 0;
}

static bool parse_worker_status_fd(const char *argument, int *descriptor) {
    const char *raw;
    char *end = NULL;
    long value;

    if (strncmp(argument, WORKER_STATUS_FD,
                sizeof(WORKER_STATUS_FD) - 1U) != 0) {
        return false;
    }
    raw = argument + sizeof(WORKER_STATUS_FD) - 1U;
    if (*raw == '\0') {
        return false;
    }
    errno = 0;
    value = strtol(raw, &end, 10);
    if (errno != 0 || end == raw || *end != '\0' ||
        value < WORKER_STATUS_DESCRIPTOR || value > INT_MAX) {
        return false;
    }
    *descriptor = (int)value;
    return true;
}

static bool parse_worker_ready_ack_fd(const char *argument, int *descriptor) {
    const char *raw;
    char *end = NULL;
    long value;

    if (strncmp(argument, WORKER_READY_ACK_FD,
                sizeof(WORKER_READY_ACK_FD) - 1U) != 0) {
        return false;
    }
    raw = argument + sizeof(WORKER_READY_ACK_FD) - 1U;
    if (*raw == '\0') {
        return false;
    }
    errno = 0;
    value = strtol(raw, &end, 10);
    if (errno != 0 || end == raw || *end != '\0' ||
        value < WORKER_STATUS_DESCRIPTOR || value > INT_MAX) {
        return false;
    }
    *descriptor = (int)value;
    return true;
}

static int open_worker_executable(const char *path) {
    static const char descriptor_prefix[] = "/proc/self/fd/";
    const char *raw;
    char *end = NULL;
    long descriptor;

    if (strncmp(path, descriptor_prefix, sizeof(descriptor_prefix) - 1U) != 0) {
        return open(path, O_PATH | O_NOFOLLOW | O_CLOEXEC);
    }
    raw = path + sizeof(descriptor_prefix) - 1U;
    if (*raw == '\0') {
        errno = EINVAL;
        return -1;
    }
    errno = 0;
    descriptor = strtol(raw, &end, 10);
    if (errno != 0 || end == raw || *end != '\0' ||
        descriptor < WORKER_STATUS_DESCRIPTOR || descriptor > INT_MAX) {
        errno = EINVAL;
        return -1;
    }
    return fcntl((int)descriptor, F_DUPFD_CLOEXEC, WORKER_STATUS_DESCRIPTOR);
}

static bool enter_worker_namespaces(void) {
    const int namespaces = CLONE_NEWUSER | CLONE_NEWNS | CLONE_NEWPID |
                           CLONE_NEWIPC | CLONE_NEWNET | CLONE_NEWCGROUP;

    return unshare(namespaces) == 0;
}

static bool bind_mount_tree(const char *path, bool readonly) {
    if (mount(path, path, NULL, MS_BIND | MS_REC, NULL) != 0) {
        return false;
    }
    if (readonly && mount(NULL, path, NULL,
                          MS_BIND | MS_REMOUNT | MS_RDONLY | MS_REC, NULL) != 0) {
        return false;
    }
    return true;
}

static bool mount_minimal_dev(void) {
    /* The closed profile declares no device nodes.  An empty tmpfs is therefore
     * the entire /dev authority; adding a host device would be a policy widen. */
    return mount("tmpfs", "/dev", "tmpfs", MS_NOSUID | MS_NOEXEC | MS_NODEV,
                 "mode=755") == 0;
}

static bool assemble_mounts(const char *subject, const char *toolchain,
                            const char *output, const char *scratch) {
    /* New propagation first: no bind/remount or tmpfs operation may escape this
     * worker's namespace.  Read-only is applied after a recursive bind, matching
     * the kernel mount API's bind-then-remount sequence. */
    return mount(NULL, "/", NULL, MS_REC | MS_PRIVATE, NULL) == 0 &&
           bind_mount_tree(subject, true) && bind_mount_tree(toolchain, true) &&
           bind_mount_tree(output, false) && bind_mount_tree(scratch, false) &&
           mount_minimal_dev();
}

static bool mount_fresh_proc(void) {
    /* CLONE_NEWPID takes effect only after fork.  Overlay proc in that child so
     * process views name the final PID namespace, never the launcher parent. */
    return mount("proc", "/proc", "proc", MS_NOSUID | MS_NOEXEC | MS_NODEV,
                 NULL) == 0;
}

static int wait_for_worker(int child) {
    int status;

    for (;;) {
        if (waitpid(child, &status, 0) >= 0) {
            break;
        }
        if (errno != EINTR) {
            return 64;
        }
    }
    if (WIFEXITED(status)) {
        return WEXITSTATUS(status);
    }
    if (WIFSIGNALED(status)) {
        return 128 + WTERMSIG(status);
    }
    return 64;
}

static bool close_worker_descriptors(int status_descriptor, int acknowledgement_descriptor) {
    long maximum;

    maximum = sysconf(_SC_OPEN_MAX);
    if (maximum < 0) {
        maximum = 65536;
    }
    for (int descriptor = 4; descriptor < maximum; descriptor++) {
        if (descriptor != status_descriptor && descriptor != acknowledgement_descriptor) {
            (void)close(descriptor);
        }
    }
    return true;
}

static void close_all_descriptors(void) {
    long maximum;

    errno = 0;
    if (syscall(SYS_close_range, 0U, UINT_MAX, 0U) == 0 || errno != ENOSYS) {
        return;
    }
    maximum = sysconf(_SC_OPEN_MAX);
    if (maximum < 0) {
        maximum = 65536;
    }
    for (int descriptor = 0; descriptor < maximum; descriptor++) {
        (void)close(descriptor);
    }
}

static int protocol_refusal(void) {
    static const char response[] =
        "{\"probes\":{},\"protocol\":\"ranex-launcher-v1\","
        "\"refusal\":\"E-C17-PROTOCOL\"}";
    (void)write_all(5, response, sizeof(response) - 1U);
    return 64;
}

static int host_fact_refusal(void) {
    static const char response[] =
        "{\"probes\":{},\"protocol\":\"ranex-launcher-v1\","
        "\"refusal\":\"E-C17-HOST-FACT-MISSING\"}";
    (void)write_all(5, response, sizeof(response) - 1U);
    return 65;
}

static bool fixed_descriptor(int descriptor, int access_mode) {
    struct stat facts;
    int flags;
    if (fstat(descriptor, &facts) != 0 || !S_ISFIFO(facts.st_mode)) {
        return false;
    }
    flags = fcntl(descriptor, F_GETFL);
    return flags >= 0 && (flags & O_ACCMODE) == access_mode;
}

static int compare_ints(const void *left, const void *right) {
    int first = *(const int *)left;
    int second = *(const int *)right;
    return (first > second) - (first < second);
}

static bool ascii_digit(char value) {
    return value >= '0' && value <= '9';
}

static size_t enumerate_unexpected_fds(int *found, size_t capacity) {
    DIR *directory = opendir("/proc/self/fd");
    struct dirent *entry;
    size_t count = 0U;
    int directory_fd;
    if (directory == NULL) {
        return SIZE_MAX;
    }
    directory_fd = dirfd(directory);
    errno = 0;
    while ((entry = readdir(directory)) != NULL) {
        char *end = NULL;
        long value;
        errno = 0;
        value = strtol(entry->d_name, &end, 10);
        if (errno != 0 || end == entry->d_name || *end != '\0') {
            continue;
        }
        if ((value < 3 || value > 5) && value != directory_fd) {
            if (count >= capacity || value > INT_MAX) {
                (void)closedir(directory);
                return SIZE_MAX;
            }
            found[count++] = (int)value;
        }
    }
    if (errno != 0 || closedir(directory) != 0) {
        return SIZE_MAX;
    }
    qsort(found, count, sizeof(found[0]), compare_ints);
    return count;
}

static bool consume_literal(char **cursor, const char *end, const char *literal) {
    size_t length = strlen(literal);
    if ((size_t)(end - *cursor) < length || memcmp(*cursor, literal, length) != 0) {
        return false;
    }
    *cursor += length;
    return true;
}

static bool parse_json_string(char **cursor, const char *end, char *output,
                              size_t capacity) {
    size_t used = 0U;
    if (*cursor == end || *(*cursor)++ != '"') {
        return false;
    }
    while (*cursor != end && **cursor != '"') {
        unsigned char value = (unsigned char)**cursor;
        if (value < 0x20U || value == '\\' || used + 1U >= capacity) {
            return false;
        }
        output[used++] = (char)value;
        (*cursor)++;
    }
    if (*cursor == end || *(*cursor)++ != '"') {
        return false;
    }
    output[used] = '\0';
    return true;
}

static bool valid_environment_name(const char *name) {
    if ((*name < 'A' || *name > 'Z') && (*name < 'a' || *name > 'z') &&
        *name != '_') {
        return false;
    }
    for (name++; *name != '\0'; name++) {
        if ((*name < 'A' || *name > 'Z') && (*name < 'a' || *name > 'z') &&
            !ascii_digit(*name) && *name != '_') {
            return false;
        }
    }
    return true;
}

static bool parse_allowlist(char **cursor, const char *end,
                            struct probe_request *request) {
    bool lc_all = false;
    bool timezone = false;
    if (*cursor == end || *(*cursor)++ != '[') {
        return false;
    }
    for (;;) {
        char *name;
        if (request->environment_count >= ENVIRONMENT_LIMIT) {
            return false;
        }
        name = request->environment_names[request->environment_count];
        if (!parse_json_string(cursor, end, name, ENVIRONMENT_NAME_LIMIT) ||
            !valid_environment_name(name)) {
            return false;
        }
        for (size_t index = 0U; index < request->environment_count; index++) {
            if (strcmp(request->environment_names[index], name) == 0) {
                return false;
            }
        }
        request->environment_count++;
        if (strcmp(name, "LC_ALL") == 0) {
            lc_all = true;
        } else if (strcmp(name, "TZ") == 0) {
            timezone = true;
        }
        if (*cursor == end) {
            return false;
        }
        if (**cursor == ']') {
            (*cursor)++;
            return lc_all && timezone;
        }
        if (*(*cursor)++ != ',') {
            return false;
        }
    }
}

static bool parse_nonnegative_long(char **cursor, const char *end, long *value) {
    char *number_end;
    if (*cursor == end || !ascii_digit(**cursor)) {
        return false;
    }
    errno = 0;
    *value = strtol(*cursor, &number_end, 10);
    if (errno != 0 || number_end > end || *value < 0) {
        return false;
    }
    *cursor = number_end;
    return true;
}

static bool parse_expected_closed(char **cursor, const char *end,
                                  struct stage_metadata *metadata) {
    int previous = -1;
    if (*cursor == end || *(*cursor)++ != '[') {
        return false;
    }
    while (*cursor != end && **cursor != ']') {
        long value;
        if (metadata->closed_count >= CLOSED_FD_LIMIT ||
            !parse_nonnegative_long(cursor, end, &value) || value > INT_MAX ||
            value <= previous) {
            return false;
        }
        metadata->closed[metadata->closed_count++] = (int)value;
        previous = (int)value;
        if (*cursor == end || (**cursor != ',' && **cursor != ']')) {
            return false;
        }
        if (**cursor == ',') {
            (*cursor)++;
        }
    }
    if (*cursor == end || *(*cursor)++ != ']') {
        return false;
    }
    return metadata->closed_count >= 3U && metadata->closed[0] == 0 &&
           metadata->closed[1] == 1 && metadata->closed[2] == 2;
}

static int read_request(struct probe_request *request) {
    char buffer[REQUEST_LIMIT + 1U];
    char *cursor;
    const char *end;
    size_t used = 0U;
    memset(request, 0, sizeof(*request));
    for (;;) {
        ssize_t received = read(4, buffer + used, sizeof(buffer) - used);
        if (received < 0 && errno == EINTR) {
            continue;
        }
        if (received < 0) {
            return -1;
        }
        if (received == 0) {
            break;
        }
        used += (size_t)received;
        if (used > REQUEST_LIMIT) {
            return -1;
        }
    }
    cursor = buffer;
    end = buffer + used;
    if (!consume_literal(&cursor, end,
                         "{\"action\":\"qualify-probe\",\"env_allowlist\":") ||
        !parse_allowlist(&cursor, end, request) ||
        !consume_literal(&cursor, end,
                         ",\"protocol\":\"ranex-launcher-v1\"}") ||
        cursor != end) {
        return -1;
    }
    return 0;
}

static long session_keyring_id(void) {
    return syscall(SYS_keyctl, KEYCTL_GET_KEYRING_ID, KEY_SPEC_SESSION_KEYRING, 0);
}

static int append_number(char *buffer, size_t capacity, size_t *used, long value) {
    int length;
    if (*used >= capacity) {
        return -1;
    }
    length = snprintf(buffer + *used, capacity - *used, "%ld", value);
    if (length < 0 || (size_t)length >= capacity - *used) {
        return -1;
    }
    *used += (size_t)length;
    return 0;
}

static char **build_environment(const struct probe_request *request) {
    char **environment = calloc(request->environment_count + 1U, sizeof(char *));
    size_t used = 0U;
    if (environment == NULL) {
        return NULL;
    }
    for (size_t index = 0U; index < request->environment_count; index++) {
        const char *name = request->environment_names[index];
        const char *value = getenv(name);
        size_t name_length;
        size_t value_length;
        size_t entry_length;
        if (value == NULL) {
            continue;
        }
        name_length = strlen(name);
        value_length = strlen(value);
        if (name_length > SIZE_MAX - value_length - 2U) {
            return NULL;
        }
        entry_length = name_length + value_length + 2U;
        environment[used] = malloc(entry_length);
        if (environment[used] == NULL ||
            snprintf(environment[used], entry_length, "%s=%s", name, value) < 0) {
            return NULL;
        }
        used++;
    }
    environment[used] = NULL;
    return environment;
}

static bool install_stage_metadata(long session_keyring_before,
                                   const char *closed_json) {
    int descriptors[2];
    char payload[REQUEST_LIMIT + 1U];
    int length = snprintf(payload, sizeof(payload), "%ld:%s", session_keyring_before,
                          closed_json);
    if (length < 0 || (size_t)length >= sizeof(payload) ||
        pipe2(descriptors, O_CLOEXEC) != 0) {
        return false;
    }
    if (write_all(descriptors[1], payload, (size_t)length) != 0 ||
        close(descriptors[1]) != 0) {
        (void)close(descriptors[0]);
        return false;
    }
    if (dup2(descriptors[0], 4) != 4) {
        (void)close(descriptors[0]);
        return false;
    }
    if (descriptors[0] != 4 && close(descriptors[0]) != 0) {
        return false;
    }
    return true;
}

static int stage_one(void) {
    struct probe_request request;
    int unexpected[CLOSED_FD_LIMIT];
    size_t unexpected_count;
    long before;
    long after;
    char *arguments[3];
    char **environment;
    char closed_argument[8192];
    size_t closed_used = 0U;

    if (!fixed_descriptor(3, O_RDONLY) || !fixed_descriptor(4, O_RDONLY) ||
        !fixed_descriptor(5, O_WRONLY)) {
        return 64;
    }
    if (read_request(&request) != 0) {
        return protocol_refusal();
    }

    unexpected_count =
        enumerate_unexpected_fds(unexpected, CLOSED_FD_LIMIT - 3U);
    if (unexpected_count == SIZE_MAX) {
        return 64;
    }
    memcpy(closed_argument, "[0,1,2", sizeof("[0,1,2") - 1U);
    closed_used = sizeof("[0,1,2") - 1U;
    for (size_t index = 0U; index < unexpected_count; index++) {
        if (unexpected[index] <= 2) {
            continue;
        }
        closed_argument[closed_used++] = ',';
        if (append_number(closed_argument, sizeof(closed_argument), &closed_used,
                          unexpected[index]) != 0) {
            return 64;
        }
    }
    if (closed_used + 2U > sizeof(closed_argument)) {
        return 64;
    }
    closed_argument[closed_used++] = ']';
    closed_argument[closed_used] = '\0';

    environment = build_environment(&request);
    if (environment == NULL) {
        return 64;
    }
    (void)close(0);
    (void)close(1);
    (void)close(2);
    errno = 0;
    int close_result = (int)syscall(SYS_close_range, 6U, UINT_MAX, 0U);
    int close_error = errno;
    if (close_result != 0 && close_error != ENOSYS) {
        return 64;
    }
    if (close_result != 0) {
        long maximum = sysconf(_SC_OPEN_MAX);
        if (maximum < 0) {
            maximum = 65536;
        }
        for (int descriptor = 6; descriptor < maximum; descriptor++) {
            (void)close(descriptor);
        }
    }

    before = session_keyring_id();
    after = syscall(SYS_keyctl, KEYCTL_JOIN_SESSION_KEYRING, 0);
    if (before < 0 || after < 0 || after == before) {
        return 64;
    }

    if (!install_stage_metadata(before, closed_argument)) {
        return 64;
    }
    arguments[0] = (char *)"ranex-worker-launcher";
    arguments[1] = (char *)STAGE_TWO;
    arguments[2] = NULL;
    execve("/proc/self/exe", arguments, environment);
    return 64;
}

static int compare_names(const void *left, const void *right) {
    return strcmp((const char *)left, (const char *)right);
}

static bool observe_environment(char *names_json, size_t names_capacity) {
    char observed[8192];
    char names[ENVIRONMENT_LIMIT][ENVIRONMENT_NAME_LIMIT];
    size_t used = 0U;
    size_t names_used = 0U;
    size_t name_count = 0U;
    int descriptor;
    descriptor = open("/proc/self/environ", O_RDONLY | O_CLOEXEC);
    if (descriptor < 0) {
        return false;
    }
    for (;;) {
        ssize_t count = read(descriptor, observed + used, sizeof(observed) - used);
        if (count < 0 && errno == EINTR) {
            continue;
        }
        if (count < 0) {
            (void)close(descriptor);
            return false;
        }
        if (count == 0) {
            break;
        }
        used += (size_t)count;
        if (used == sizeof(observed)) {
            (void)close(descriptor);
            return false;
        }
    }
    if (close(descriptor) != 0) {
        return false;
    }
    for (size_t offset = 0U; offset < used;) {
        char *assignment = observed + offset;
        size_t assignment_length = strnlen(assignment, used - offset);
        char *separator;
        size_t name_length;
        if (assignment_length == used - offset || name_count >= ENVIRONMENT_LIMIT) {
            return false;
        }
        separator = memchr(assignment, '=', assignment_length);
        if (separator == NULL) {
            return false;
        }
        name_length = (size_t)(separator - assignment);
        if (name_length == 0U || name_length >= ENVIRONMENT_NAME_LIMIT) {
            return false;
        }
        memcpy(names[name_count], assignment, name_length);
        names[name_count][name_length] = '\0';
        if (!valid_environment_name(names[name_count])) {
            return false;
        }
        name_count++;
        offset += assignment_length + 1U;
    }
    qsort(names, name_count, sizeof(names[0]), compare_names);
    if (names_capacity < 3U) {
        return false;
    }
    names_json[names_used++] = '[';
    for (size_t index = 0U; index < name_count; index++) {
        size_t name_length = strlen(names[index]);
        size_t required = name_length + (index == 0U ? 2U : 3U);
        if (required >= names_capacity - names_used) {
            return false;
        }
        if (index != 0U) {
            names_json[names_used++] = ',';
        }
        names_json[names_used++] = '"';
        memcpy(names_json + names_used, names[index], name_length);
        names_used += name_length;
        names_json[names_used++] = '"';
    }
    names_json[names_used++] = ']';
    names_json[names_used] = '\0';
    return true;
}

static bool status_facts(int *no_new_privs) {
    char buffer[8192];
    ssize_t count;
    int descriptor = open("/proc/self/status", O_RDONLY | O_CLOEXEC);
    char *nnp;
    if (descriptor < 0) {
        return false;
    }
    count = read(descriptor, buffer, sizeof(buffer) - 1U);
    (void)close(descriptor);
    if (count <= 0 || (size_t)count == sizeof(buffer) - 1U) {
        return false;
    }
    buffer[count] = '\0';
    if (strstr(buffer, "Seccomp:") == NULL || strstr(buffer, "Seccomp_filters:") == NULL) {
        return false;
    }
    nnp = strstr(buffer, "NoNewPrivs:");
    if (nnp == NULL || sscanf(nnp, "NoNewPrivs:\t%d", no_new_privs) != 1) {
        return false;
    }
    return true;
}

static bool descriptor_absent(int descriptor) {
    errno = 0;
    return fcntl(descriptor, F_GETFD) == -1 && errno == EBADF;
}

static bool read_stage_metadata(struct stage_metadata *metadata) {
    char buffer[REQUEST_LIMIT + 1U];
    char *cursor;
    const char *end;
    size_t used = 0U;
    memset(metadata, 0, sizeof(*metadata));
    for (;;) {
        ssize_t received = read(4, buffer + used, sizeof(buffer) - used);
        if (received < 0 && errno == EINTR) {
            continue;
        }
        if (received < 0) {
            return false;
        }
        if (received == 0) {
            break;
        }
        used += (size_t)received;
        if (used > REQUEST_LIMIT) {
            return false;
        }
    }
    buffer[used] = '\0';
    cursor = buffer;
    end = buffer + used;
    if (!parse_nonnegative_long(&cursor, end, &metadata->session_keyring_before) ||
        metadata->session_keyring_before <= 0 || !consume_literal(&cursor, end, ":")) {
        return false;
    }
    return parse_expected_closed(&cursor, end, metadata) && cursor == end;
}

static int stage_two(int argc, char **argv) {
    struct stage_metadata metadata;
    int unexpected[CLOSED_FD_LIMIT];
    size_t unexpected_count;
    char gate;
    char response[RESPONSE_LIMIT];
    char closed_json[8192];
    char observed_names_json[8192];
    size_t closed_used = 0U;
    long after;
    int no_new_privs = 0;
    long landlock_abi;
    int length;
    bool exact_fd_set;
    bool secret_absent;

    if (argc != 2 || strcmp(argv[1], STAGE_TWO) != 0 ||
        !fixed_descriptor(3, O_RDONLY) || !fixed_descriptor(4, O_RDONLY) ||
        !fixed_descriptor(5, O_WRONLY)) {
        return protocol_refusal();
    }
    if (!read_stage_metadata(&metadata)) {
        return protocol_refusal();
    }
    unexpected_count = enumerate_unexpected_fds(unexpected, CLOSED_FD_LIMIT);
    exact_fd_set = unexpected_count == 0U;
    if (unexpected_count == SIZE_MAX || !exact_fd_set) {
        return 64;
    }
    after = session_keyring_id();
    if (after <= 0 ||
        !observe_environment(observed_names_json, sizeof(observed_names_json)) ||
        prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0) {
        return 64;
    }
    secret_absent = getenv(INJECTED_SECRET_NAME) == NULL;

    closed_json[closed_used++] = '[';
    for (size_t index = 0U; index < metadata.closed_count; index++) {
        int descriptor = metadata.closed[index];
        if (!descriptor_absent(descriptor)) {
            return host_fact_refusal();
        }
        if (index != 0U) {
            closed_json[closed_used++] = ',';
        }
        if (append_number(closed_json, sizeof(closed_json), &closed_used, descriptor) != 0) {
            return protocol_refusal();
        }
    }
    if (closed_used + 2U > sizeof(closed_json)) {
        return protocol_refusal();
    }
    closed_json[closed_used++] = ']';
    closed_json[closed_used] = '\0';

    if (after == metadata.session_keyring_before) {
        return host_fact_refusal();
    }
    for (;;) {
        ssize_t received = read(3, &gate, 1U);
        if (received < 0 && errno == EINTR) {
            continue;
        }
        if (received != 1) {
            return protocol_refusal();
        }
        break;
    }

    landlock_abi = syscall(SYS_landlock_create_ruleset, NULL, 0U,
                           LANDLOCK_CREATE_RULESET_VERSION);
    if (landlock_abi < REQUIRED_LANDLOCK_ABI || !exact_fd_set ||
        session_keyring_id() != after || !status_facts(&no_new_privs) ||
        no_new_privs != 1) {
        return host_fact_refusal();
    }

    length = snprintf(
        response, sizeof(response),
        "{\"probes\":{\"closed_unexpected_fds\":%s,"
        "\"inherited_session_keyring_invalidated\":true,"
        "\"injected_secret_env_absent\":%s,"
        "\"injected_unexpected_fd_absent\":%s,\"landlock_abi\":%ld,"
        "\"no_new_privs\":1,\"observed_env_names\":%s,"
        "\"seccomp_fields_present\":true,\"session_keyring_after\":%ld,"
        "\"session_keyring_before\":%ld},\"protocol\":"
        "\"ranex-launcher-v1\",\"refusal\":null}",
        closed_json, secret_absent ? "true" : "false",
        exact_fd_set ? "true" : "false", landlock_abi, observed_names_json, after,
        metadata.session_keyring_before);
    if (length < 0 || (size_t)length >= sizeof(response)) {
        return protocol_refusal();
    }
    if (write_all(5, response, (size_t)length) != 0) {
        return 66;
    }
    return 0;
}

/*
 * Execute a single already-resolved worker beneath its sole writable directory.
 * This is deliberately a separate, closed invocation from the qualification
 * protocol: qualification never accepts a command payload.
 */
static int worker_exec(int argc, char **argv) {
    struct probe_request worker_environment_request = {
        .environment_names = {"LC_ALL", "TZ"},
        .environment_count = 2U,
    };
    int subject_fd = -1;
    int toolchain_fd = -1;
    int output_fd = -1;
    int scratch_fd = -1;
    int executable_fd;
    int status_descriptor = -1;
    int acknowledgement_descriptor = -1;
    int argument_offset = 2;
    int pid_pipe[2];
    pid_t worker;
    long controller_visible_pid;
    char **environment;
    char readiness[256];
    int readiness_length;

    while (argc > argument_offset && strncmp(argv[argument_offset], "--ranex-", 8U) == 0) {
        if (strncmp(argv[argument_offset], WORKER_STATUS_FD,
                    sizeof(WORKER_STATUS_FD) - 1U) == 0) {
            if (status_descriptor >= 0 ||
                !parse_worker_status_fd(argv[argument_offset], &status_descriptor)) {
                return 64;
            }
        } else if (strncmp(argv[argument_offset], WORKER_READY_ACK_FD,
                           sizeof(WORKER_READY_ACK_FD) - 1U) == 0) {
            if (acknowledgement_descriptor >= 0 ||
                !parse_worker_ready_ack_fd(argv[argument_offset], &acknowledgement_descriptor)) {
                return 64;
            }
        } else {
            return 64;
        }
        argument_offset++;
    }
    if (status_descriptor >= 0 &&
        (acknowledgement_descriptor < 0 || acknowledgement_descriptor == status_descriptor)) {
        return 64;
    }
    if (argc < argument_offset + 5 || argv[argument_offset][0] != '/' ||
        argv[argument_offset + 1][0] != '/' || argv[argument_offset + 2][0] != '/' ||
        argv[argument_offset + 3][0] != '/' || argv[argument_offset + 4][0] != '/') {
        return 64;
    }
    subject_fd = open(argv[argument_offset], O_PATH | O_DIRECTORY | O_CLOEXEC);
    toolchain_fd = open(argv[argument_offset + 1], O_PATH | O_DIRECTORY | O_CLOEXEC);
    output_fd = open(argv[argument_offset + 2], O_PATH | O_DIRECTORY | O_CLOEXEC);
    scratch_fd = open(argv[argument_offset + 3], O_PATH | O_DIRECTORY | O_CLOEXEC);
    executable_fd = open_worker_executable(argv[argument_offset + 4]);
    if (subject_fd < 0 || toolchain_fd < 0 || output_fd < 0 || scratch_fd < 0 ||
        executable_fd < 0) {
        (void)close(subject_fd);
        (void)close(toolchain_fd);
        (void)close(output_fd);
        (void)close(scratch_fd);
        (void)close(executable_fd);
        return 64;
    }
    environment = build_environment(&worker_environment_request);
    if (environment == NULL) {
        (void)close(subject_fd);
        (void)close(toolchain_fd);
        (void)close(output_fd);
        (void)close(scratch_fd);
        (void)close(executable_fd);
        return 64;
    }
    /* CLONE_NEWPID takes effect in this forked child; the outer launcher only
     * waits and relays its exit status, so the command itself owns every
     * namespace named in the readiness record.  Mount propagation and all
     * descriptor-tree mounts happen before the fork; proc must wait until it. */
    if (!enter_worker_namespaces()) {
        (void)close(subject_fd);
        (void)close(toolchain_fd);
        (void)close(output_fd);
        (void)close(scratch_fd);
        (void)close(executable_fd);
        return 64;
    }
    if (!assemble_mounts(argv[argument_offset], argv[argument_offset + 1],
                         argv[argument_offset + 2], argv[argument_offset + 3])) {
        (void)close(subject_fd);
        (void)close(toolchain_fd);
        (void)close(output_fd);
        (void)close(scratch_fd);
        (void)close(executable_fd);
        return 64;
    }
    if (pipe2(pid_pipe, O_CLOEXEC) != 0) {
        (void)close(subject_fd);
        (void)close(toolchain_fd);
        (void)close(output_fd);
        (void)close(scratch_fd);
        (void)close(executable_fd);
        return 64;
    }
    worker = fork();
    if (worker < 0) {
        (void)close(pid_pipe[0]);
        (void)close(pid_pipe[1]);
        (void)close(subject_fd);
        (void)close(toolchain_fd);
        (void)close(output_fd);
        (void)close(scratch_fd);
        (void)close(executable_fd);
        return 64;
    }
    if (worker > 0) {
        controller_visible_pid = (long)worker;
        (void)close(pid_pipe[0]);
        if (write_all(pid_pipe[1], (const char *)&controller_visible_pid,
                      sizeof(controller_visible_pid)) != 0) {
            (void)close(pid_pipe[1]);
            return 64;
        }
        (void)close(pid_pipe[1]);
        (void)close(subject_fd);
        (void)close(toolchain_fd);
        (void)close(output_fd);
        (void)close(scratch_fd);
        (void)close(executable_fd);
        if (status_descriptor >= 0) {
            (void)close(status_descriptor);
        }
        close_all_descriptors();
        return wait_for_worker(worker);
    }
    (void)close(pid_pipe[1]);
    if (read(pid_pipe[0], &controller_visible_pid,
             sizeof(controller_visible_pid)) != (ssize_t)sizeof(controller_visible_pid) ||
        close(pid_pipe[0]) != 0 || controller_visible_pid <= 0) {
        (void)close(subject_fd);
        (void)close(toolchain_fd);
        (void)close(output_fd);
        (void)close(scratch_fd);
        (void)close(executable_fd);
        return 64;
    }
    if (!mount_fresh_proc() || fchdir(scratch_fd) != 0 ||
        prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0 ||
        !enforce_landlock(executable_fd, subject_fd, toolchain_fd, output_fd, scratch_fd)) {
        (void)close(subject_fd);
        (void)close(toolchain_fd);
        (void)close(output_fd);
        (void)close(scratch_fd);
        (void)close(executable_fd);
        return 64;
    }

    /* Keep the executable on a fixed descriptor, then remove every inherited
     * authority.  This is stage one's close discipline with its protocol FDs
     * replaced by the sole object needed by execveat. */
    if (executable_fd != 3 && dup2(executable_fd, 3) != 3) {
        (void)close(subject_fd);
        (void)close(toolchain_fd);
        (void)close(output_fd);
        (void)close(scratch_fd);
        (void)close(executable_fd);
        return 64;
    }
    if ((subject_fd != 3 && close(subject_fd) != 0) ||
        (toolchain_fd != 3 && close(toolchain_fd) != 0) ||
        (output_fd != 3 && close(output_fd) != 0) ||
        (scratch_fd != 3 && close(scratch_fd) != 0)) {
        (void)close(executable_fd);
        return 64;
    }
    if (executable_fd != 3 && close(executable_fd) != 0) {
        return 64;
    }
    (void)close(0);
    (void)close(1);
    (void)close(2);
    if (!close_worker_descriptors(status_descriptor, acknowledgement_descriptor)) {
        return 64;
    }
    if (!enforce_seccomp()) {
        return 64;
    }
    if (status_descriptor >= 0) {
        readiness_length = snprintf(readiness, sizeof(readiness),
                                     WORKER_READY_PREFIX "%ld" WORKER_READY_SUFFIX,
                                    controller_visible_pid);
        if (readiness_length < 0 || (size_t)readiness_length >= sizeof(readiness) ||
            write_all(status_descriptor, readiness, (size_t)readiness_length) != 0 ||
            close(status_descriptor) != 0) {
            return 64;
        }
    }
    if (acknowledgement_descriptor >= 0) {
        char acknowledgement;

        if (read(acknowledgement_descriptor, &acknowledgement, 1U) != 1 ||
            acknowledgement != '1' || close(acknowledgement_descriptor) != 0) {
            return 64;
        }
    }

    /* AT_EMPTY_PATH binds exec to the same object Landlock admitted. */
    (void)syscall(SYS_execveat, 3, "", argv + argument_offset + 4, environment,
                  AT_EMPTY_PATH);
    (void)close(3);
    return 64;
}

int main(int argc, char **argv) {
    if (argc == 1) {
        return stage_one();
    }
    if (argc >= 2 && strcmp(argv[1], STAGE_TWO) == 0) {
        return stage_two(argc, argv);
    }
    if (argc >= 2 && strcmp(argv[1], WORKER_EXEC) == 0) {
        return worker_exec(argc, argv);
    }
    return protocol_refusal();
}
