#include <errno.h>
#include <fcntl.h>
#include <stddef.h>
#include <string.h>
#include <sys/mount.h>
#include <sys/stat.h>
#include <unistd.h>

static int copy_exact(const char *source, const char *destination) {
    char buffer[256];
    int input = open(source, O_RDONLY | O_CLOEXEC);
    int output = open(destination, O_WRONLY | O_CREAT | O_EXCL | O_CLOEXEC, 0600);
    ssize_t count;

    if (input < 0 || output < 0) return 70;
    while ((count = read(input, buffer, sizeof(buffer))) > 0) {
        char *cursor = buffer;
        while (count > 0) {
            ssize_t written = write(output, cursor, (size_t)count);
            if (written <= 0) return 71;
            cursor += written;
            count -= written;
        }
    }
    if (count < 0 || close(input) != 0 || close(output) != 0) return 72;
    return 0;
}

int main(int argc, char **argv) {
    if (argc == 3) return copy_exact(argv[1], argv[2]);
    if (argc == 5 && strcmp(argv[1], "--require-authority-read-only") == 0) {
        int input_write = open(argv[2], O_WRONLY | O_CLOEXEC);
        if (input_write >= 0) return 73;
        if (errno != EROFS && errno != EACCES) return 74;
        int toolchain_write = open(argv[3], O_WRONLY | O_CLOEXEC);
        if (toolchain_write >= 0) return 75;
        if (errno != EROFS && errno != EACCES) return 76;
        if (mkdir("/ranex/scratch/escape", 0700) != 0) return 77;
        if (mount("/ranex/subject", "/ranex/scratch/escape", NULL, MS_BIND, NULL) == 0) {
            return 78;
        }
        if (errno != EPERM && errno != ENOSYS) return 79;
        return copy_exact(argv[2], argv[4]);
    }
    if (argc != 4) return 64;
    if (strcmp(argv[1], "--require-input-read-only") != 0) return 65;
    int forbidden = open(argv[2], O_WRONLY | O_CLOEXEC);
    if (forbidden >= 0) {
        close(forbidden);
        return 73;
    }
    if (errno != EROFS && errno != EACCES) return 74;
    return copy_exact(argv[2], argv[3]);
}
