#include <arpa/inet.h>
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/prctl.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <time.h>
#include <unistd.h>

#define INPUT_PATH "/ranex/input/task.json"
#define OUTPUT_PATH "/ranex/output/result.json"
#define INPUT_LIMIT 512
#define OUTPUT_LIMIT 512

static int refuse_input(void) {
    static const char refusal[] =
        "{\"code\":\"E-BATCH-INPUT-MISMATCH\",\"event\":\"batch.child.refused\"}\n";
    if (write(STDOUT_FILENO, refusal, sizeof(refusal) - 1U) < 0) return 96;
    return 92;
}

static bool closed_word(const char *value, const char *a, const char *b,
                        const char *c, const char *d) {
    return strcmp(value, a) == 0 || strcmp(value, b) == 0 ||
           strcmp(value, c) == 0 || strcmp(value, d) == 0;
}

static int connect_loopback(void) {
    for (uint16_t port = 46120; port <= 46135; ++port) {
        int fd = socket(AF_INET, SOCK_STREAM | SOCK_CLOEXEC, 0);
        struct sockaddr_in address = {
            .sin_family = AF_INET,
            .sin_port = htons(port),
            .sin_addr = {.s_addr = htonl(INADDR_LOOPBACK)},
        };
        if (fd >= 0) {
            int connected = connect(fd, (const struct sockaddr *)&address,
                                    sizeof(address));
            (void)close(fd);
            if (connected == 0) return 1;
        }
    }
    return 0;
}

static pid_t start_survivor(void) {
    pid_t pid = fork();
    if (pid != 0) return pid;
    (void)setsid();
    (void)prctl(PR_SET_NAME, "ranex-slice036", 0, 0, 0);
    struct timespec interval = {.tv_sec = 30, .tv_nsec = 0};
    while (nanosleep(&interval, &interval) < 0 && errno == EINTR) {}
    _exit(0);
}

static int write_all(int fd, const char *bytes, size_t length) {
    while (length != 0U) {
        ssize_t written = write(fd, bytes, length);
        if (written < 0 && errno == EINTR) continue;
        if (written <= 0) return -1;
        bytes += written;
        length -= (size_t)written;
    }
    return 0;
}

int main(int argc, char **argv) {
    char input[INPUT_LIMIT];
    char task_id[64] = {0};
    char flow_id[32] = {0};
    char mode[32] = {0};
    char trailing = '\0';
    unsigned attempt = 0;
    unsigned delay_ms = 0;
    if (argc != 2 || strcmp(argv[1], "--task") != 0) return 64;
    int input_fd = open(INPUT_PATH, O_RDONLY | O_CLOEXEC | O_NOFOLLOW);
    if (input_fd < 0) return refuse_input();
    ssize_t length = read(input_fd, input, sizeof(input) - 1U);
    if (length <= 0 || close(input_fd) != 0) return refuse_input();
    input[length] = '\0';
    int fields = sscanf(
        input,
        "{\"attempt\":%u,\"delay_ms\":%u,\"flow_id\":\"%31[A-Za-z0-9-]\","
        "\"mode\":\"%31[A-Za-z0-9-]\",\"task_id\":\"%63[A-Za-z0-9-]\","
        "\"version\":\"slice036-child-input-v2\"}%c",
        &attempt, &delay_ms, flow_id, mode, task_id, &trailing);
    if (fields != 5 || attempt > 6 || delay_ms > 5000 ||
        !closed_word(flow_id, "a-before-b", "b-before-a", "network-control",
                     "survivor-control") ||
        !closed_word(mode, "normal", "network-control", "survivor",
                     "oracle-mismatch") ||
        strncmp(task_id, "SLICE-036-child-", 16) != 0 || strlen(task_id) != 17) {
        return refuse_input();
    }

    struct timespec delay = {
        .tv_sec = (time_t)(delay_ms / 1000U),
        .tv_nsec = (long)(delay_ms % 1000U) * 1000000L,
    };
    while (nanosleep(&delay, &delay) < 0 && errno == EINTR) {}
    int escaped = connect_loopback();
    pid_t survivor = mode[0] == 's' ? start_survivor() : 0;
    if (survivor < 0) return 93;

    const char *value = strcmp(mode, "oracle-mismatch") == 0
                            ? "oracle-mismatch"
                            : "ok";
    char output[OUTPUT_LIMIT];
    char pid_text[32] = "null";
    if (survivor != 0 && snprintf(pid_text, sizeof(pid_text), "%ld",
                                  (long)survivor) < 0) {
        return 94;
    }
    int output_length = snprintf(
        output, sizeof(output),
        "{\"attempt\":%u,\"flow_id\":\"%s\",\"network\":\"%s\","
        "\"pid\":%s,\"task_id\":\"%s\",\"value\":\"%s\"}\n",
        attempt, flow_id, escaped ? "escaped" : "denied",
        pid_text, task_id, value);
    if (output_length < 0 || (size_t)output_length >= sizeof(output)) return 94;
    int output_fd = open(OUTPUT_PATH,
                         O_WRONLY | O_CREAT | O_EXCL | O_CLOEXEC | O_NOFOLLOW,
                         0600);
    if (output_fd < 0 ||
        write_all(output_fd, output, (size_t)output_length) != 0 ||
        close(output_fd) != 0 ||
        write_all(STDOUT_FILENO, output, (size_t)output_length) != 0) {
        return 95;
    }
    return escaped || strcmp(mode, "network-control") == 0 ? 91 : 0;
}
