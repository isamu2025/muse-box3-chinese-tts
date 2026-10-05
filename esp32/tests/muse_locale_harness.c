/* SPDX-License-Identifier: Apache-2.0 */
#include "muse_locale.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef _WIN32
#include <fcntl.h>
#include <io.h>
#endif
int main(int argc, char **argv)
{
#ifdef _WIN32
    _setmode(_fileno(stdin), _O_BINARY);
    _setmode(_fileno(stdout), _O_BINARY);
#endif
    if (argc < 2) return 2;
    char input[512], buf[128];
    if (!fgets(input, sizeof(input), stdin)) return 3;
    input[strcspn(input, "\r\n")] = 0;
    const char *result;
    if (strcmp(argv[1], "status") == 0) result = muse_ui_status_text(input);
    else if (strcmp(argv[1], "error") == 0) result = muse_ui_error_text(input);
    else if (strcmp(argv[1], "button") == 0) result = muse_ui_button_name(input);
    else {
        unsigned size = argc > 2 ? (unsigned)atoi(argv[2]) : sizeof(buf);
        if (size > sizeof(buf)) return 4;
        result = muse_ui_detail_text(input, buf, size);
    }
    fputs(result, stdout);
    return 0;
}
