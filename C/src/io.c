#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAXLEN 32

int main() {
    setbuf(stdout, NULL); // no buffer!

    int a;
    char b;
    long c;
    char d[MAXLEN] = {0};

    printf("Input an integer: ");
    scanf("%d", &a);
    printf("You entered: '%d'\n", a);

    printf("Input a character: ");
    scanf(" %c", &b);
    printf("You entered: '%c'\n", b);

    printf("Input a long integer: ");
    scanf("%ld%*c", &c);
    printf("You entered: '%ld'\n", c);

    printf("Input a string (maximum length: %u): ", MAXLEN);
    fgets(d, MAXLEN, stdin);
    size_t len = strlen(d);
    if ((len > 0) && (d[len - 1] == '\n'))
        d[len - 1] = 0;
    printf("You entered: '%s'\n", d);

    return 0;
}