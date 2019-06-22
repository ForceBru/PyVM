#define assert(some_bool, code) do { if (!(some_bool)) return (code); } while(0)

struct Huge {
    char a;
    int b;
    long c;
    long long d;
    unsigned char e;
    unsigned int f;
    unsigned long g;
    unsigned long long h;
};

int main(void) {
    struct Huge test1 = {
        .a='y', .b=-75647, .c=-756478, .d=79647801,
        .e='z', .f=75641,  .g=258454,  .h=12345678901
    };

    assert(test1.a == 'y'        , 1);
    assert(test1.b == -75647     , 2);
    assert(test1.c == -756478    , 3);
    assert(test1.d ==  79647801  , 4);

    assert(test1.e == 'z'        , 5);
    assert(test1.f == 75641      , 6);
    assert(test1.g == 258454     , 7);
    assert(test1.h == 12345678901, 8);

    struct Huge test2;
    test2.a = test1.a - 5;
    test2.b = test1.b + test1.f;
    test2.c = test1.c + test1.g;

    assert(test2.a == (test1.a - 5)      ,  9);
    assert(test2.b == (int)(test1.b + test1.f), 10);
    assert(test2.c == (long)(test1.c + test1.g), 11);

    return 0;
}
