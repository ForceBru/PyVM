#include <stdio.h>

#define MAX_STACK 1024

int main() {
    int stack[MAX_STACK];
    int sp = 0;

    puts("Reverse polish notation calculator.");
    puts("Usage: input looks like '3 2 - 5 * ='. Then press Enter. Repeat ad nauseum. Input 'q' to quit.");

    while ( !feof(stdin) ) {
        int c = getchar();
        int x;

        switch (c) {
            case  ' ':
            case '\n':
                break;
            case '=':
                printf("Result = %d\n", stack[sp - 1]);
                sp--;
                break;
            case '+':
                stack[sp-2] = stack[sp-2] + stack[sp-1];
                sp--;
                break;
            case '-':
                stack[sp-2] = stack[sp-2] - stack[sp-1];
                sp--;
                break;
            case '*':
                stack[sp-2] = stack[sp-1] * stack[sp-2];
                sp--;
                break;
            case '/':
                stack[sp-2] = stack[sp-2] / stack[sp-1];
                sp--;
                break;
            case 'q':
                puts("Quitting...");
                return 0;
            default:
                ungetc (c, stdin);
                if (scanf("%d", &x) != 1) {
                    fprintf(stderr, "Can't read integer, exiting!\n");
                    return -1;
                } else {
                    if (sp + 1 == MAX_STACK) {
                        fprintf(stderr, "Stack overflow (max number of numbers: %d), exiting!\n", MAX_STACK);
                    }
                    stack[sp++] = x;
                }
        }
    }
    printf("Result = %d\n",stack[sp-1]);
    return 0;
}
