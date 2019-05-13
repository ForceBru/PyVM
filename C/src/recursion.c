unsigned long long factorial(unsigned long long x) {
    if (x == 0)
        return 1;

    return x * factorial(x - 1);
}

#define NTESTS 21

int main(void) {
    unsigned long long factorials[NTESTS] = {
        1,
        1,
        2,
        6,
        24,
        120,
        720,
        5040,
        40320,
        362880,
        3628800,
        39916800,
        479001600,
        6227020800,
        87178291200,
        1307674368000,
        20922789888000,
        355687428096000,
        6402373705728000,
        121645100408832000,
        2432902008176640000
    };

    for (unsigned int i = 0; i < NTESTS; ++i) {
        unsigned long long ret = factorial(i);

        if (ret != factorials[i])
            return i + 1;
    }

    return 0;
}
