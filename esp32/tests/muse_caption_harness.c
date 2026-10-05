/* Host driver for the real caption pager; no device or Muse connection needed. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "muse_chat_priv.h"
#include "muse_text.h"
#ifdef _WIN32
#include <fcntl.h>
#include <io.h>
#endif

void muse_state_page(int *cols, int *lines)
{
    *cols = 19;
    *lines = 2;
}

int main(int argc, char **argv)
{
#ifdef _WIN32
    _setmode(_fileno(stdin), _O_BINARY);
    _setmode(_fileno(stdout), _O_BINARY);
#endif
    char text[8192], caption[400];
    size_t n = fread(text, 1, sizeof(text) - 1, stdin);
    text[n] = '\0';
    if (argc != 2) return 2;
    if (!muse_hatch_caption_at(text, strtoul(argv[1], NULL, 10), caption, sizeof(caption))) return 3;
    muse_text_to_ascii(caption, sizeof(caption));
    fwrite(caption, 1, strlen(caption), stdout);
    return 0;
}
