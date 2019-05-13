#include <stdio.h>
#include <string.h>

#define OP_LEN 8

int main(void) {
    setbuf(stdout, NULL); // no buffer!

    long long a, b, c;
    char str_a[OP_LEN] = {0}, str_b[OP_LEN] = {0}, op = 0;

    puts("This is a simple calculator. It supports only binary operators on integers.");
    puts("Use 'r' to refer to the result of the last operation, 'q' to quit.");
    puts("Available operators: +, -, *, /");

    while (1) {
        printf("First operand: ");
        fgets(str_a, OP_LEN, stdin);

        if (str_a[0] == 'q')
            break;

        size_t len = strlen(str_a);
        if (len && (str_a[len - 1] == '\n'))
            str_a[len - 1] = 0;

        printf("Operation: ");
        scanf("%c%*c", &op);

        if (op == 'q')
            break;

        printf("Second operand: ");
        fgets(str_b, OP_LEN, stdin);

        if (str_b[0] == 'q')
            break;

        len = strlen(str_b);
        if (len && (str_b[len - 1] == '\n'))
            str_b[len - 1] = 0;

        if (str_a[0] == 'r')
            a = c;
        else
            sscanf(str_a, "%lld", &a);

        if (str_b[0] == 'r')
            b = c;
        else
            sscanf(str_b, "%lld", &b);

        switch (op) {
            case '+':
                c = a + b;
                break;
            case '-':
                c = a - b;
                break;
            case '*':
                c = a * b;
                break;
            case '/':
                c = a / b;
                break;
            default:
                printf("[ERR] Invalid operation: '%c'", op);
                return -1;
        }

        printf("[ANS] %lld\n", c);

        memset(str_a, 0, OP_LEN);
        memset(str_b, 0, OP_LEN);
    }

    return 0;
}
