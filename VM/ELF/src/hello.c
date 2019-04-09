#include "stdio.h"
#include "string.h"

#define MAX_INPUT 255

const char *data = "Hello, world!";
const char *input_prompt = "Input something: ";
const char *output_prompt = "You entered: ";

int main(void) {
    char input[MAX_INPUT] = {0};

    puts(data);

    fputs(input_prompt, stdout);
    fgets(input, MAX_INPUT, stdin);

    fputs(output_prompt, stdout);

    return fputs(input, stdout);
}