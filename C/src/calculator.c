#include <stdio.h>
#include <string.h>
#include <stdlib.h> // atoll

#define OP_LEN 8

long long process_operand(char *string, long long ans) {
    size_t len = strlen(string);
    if (len && (string[len - 1] == '\n'))
        string[len - 1] = 0;

    if (string[0] == 'r')
        return ans;
    return atoll(string);
}

char process_operation(char op, char *valid_ops, size_t n_valid_ops) {
    for (size_t i = 0; i < n_valid_ops; ++i) {
        if (op == valid_ops[i])
            return 1;
    }
    printf("[ERR] Invalid operation: '%c'\n", op);
    return 0;
}

static const char valid_ops[] = "+-*/";
static const size_t n_valid_ops = sizeof valid_ops / sizeof valid_ops[0];

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

        a = process_operand(str_a, c);

        printf("Operation: ");
        scanf("%c%*c", &op);

        if (op == 'q')
            break;

        if (! process_operation(op, (char *)valid_ops, n_valid_ops))
            continue;

        printf("Second operand: ");
        fgets(str_b, OP_LEN, stdin);

        if (str_b[0] == 'q')
            break;

        b = process_operand(str_b, c);

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
                printf("[ERR] Invalid operation: '%c'\n", op);
                continue;
        }

        printf("[ANS] %lld\n", c);

        memset(str_a, 0, OP_LEN);
        memset(str_b, 0, OP_LEN);
    }

    return 0;
}
