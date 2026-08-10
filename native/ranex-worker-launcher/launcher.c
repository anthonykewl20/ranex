#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <linux/keyctl.h>
#include <linux/landlock.h>
#include <limits.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/prctl.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <sys/types.h>
#include <unistd.h>

#define REQUEST_LIMIT 4096U
#define RESPONSE_LIMIT 65536U
#define REQUIRED_LANDLOCK_ABI 6
#define STAGE_TWO "--ranex-internal-stage-two"
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

int main(int argc, char **argv) {
    if (argc == 1) {
        return stage_one();
    }
    if (argc >= 2 && strcmp(argv[1], STAGE_TWO) == 0) {
        return stage_two(argc, argv);
    }
    return protocol_refusal();
}
