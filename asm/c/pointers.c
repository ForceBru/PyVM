void change_data(int *data) {
    *data = 1;
}

int main(void) {
    int a = 5;

    change_data(&a);

    return a;
}