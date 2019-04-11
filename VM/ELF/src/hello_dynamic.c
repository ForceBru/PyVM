#include "stdio.h"
#include "stdlib.h"
#include "string.h"

#define MAX_SIZE 512

int main(void) {
    char *data = calloc(MAX_SIZE, sizeof(char));
    if (data == NULL) {
        puts("Failed to allocate memory for `data`!");
        return -1;
    }

    char *after_message = calloc(MAX_SIZE / 8, sizeof(char));
    if (after_message == NULL) {
        puts("Failed to allocate memory for `after_message`!");
        return -1;
    }

    char *initial_data = data;

    memset(data, 0, MAX_SIZE);
    memset(after_message, 0, MAX_SIZE / 8);

    char *msg_1 = strdup("Hey, ");
    if (msg_1 == NULL) {
        puts("Failed to allocate memory for `msg_1`!");
        return -1;
    }

    strcpy(data, msg_1);
    data += strlen(msg_1);

    strcpy(after_message, "! You are awesome!");

    char *msg_2 = strdup("Enter your name: ");
    if (msg_2 == NULL) {
        puts("Failed to allocate memory for `msg_2`!");
        return -1;
    }

    fputs(msg_2, stdout);

    char *name = fgets(data, MAX_SIZE, stdin);

    size_t name_length = strlen(name);
    if (name_length) {
        name[--name_length] = 0;  // get rid of newline
    }

    fputs(initial_data, stdout);
    puts(after_message);

    // deallocate in random order
    free(msg_2);
    free(msg_1);
    free(after_message);
    free(initial_data);

    return name_length;
}