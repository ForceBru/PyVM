#include "stdio.h"
#include "stdlib.h"
#include "string.h"

#define MAX_SIZE 512

int main(void) {
    char *data = calloc(MAX_SIZE, sizeof(char));
    char *after_message = calloc(MAX_SIZE / 8, sizeof(char));
    char *msg_1 = strdup("Hey, ");
    char *msg_2 = strdup("Enter your name: ");

    // deallocate in random order
    free(msg_2);
    free(msg_1);
    free(after_message);
    free(data);

    return 0;
}