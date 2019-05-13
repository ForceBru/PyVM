#include <string.h>

#define createArray(type, number) type array##number[] = \
{  0,   1,   2,   3,   4,   5,   6,   7,   8,   9, \
  10,  11,  12,  13,  14,  15,  16,  17,  18,  19, \
  20,  21,  22,  23,  24,  25,  26,  27,  28,  29, \
  30,  31,  32,  33,  34,  35,  36,  37,  38,  39, \
  40,  41,  42,  43,  44,  45,  46,  47,  48,  49, \
  50,  51,  52,  53,  54,  55,  56,  57,  58,  59, \
  60,  61,  62,  63,  64,  65,  66,  67,  68,  69, \
  70,  71,  72,  73,  74,  75,  76,  77,  78,  79, \
  80,  81,  82,  83,  84,  85,  86,  87,  88,  89, \
  90,  91,  92,  93,  94,  95,  96,  97,  98,  99, \
 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, \
 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, \
 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, \
 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, \
 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, \
 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, \
 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, \
 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, \
 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, \
 190, 191, 192, 193, 194, 195, 196, 197, 198, 199}

#define emptyArray(type, number) type array##number[sizeof array1]
#define doMemcpy(to, from) memcpy(array##to, array##from, sizeof array##from)
#define doMemset(number) memset(array##number, 0, sizeof array##number)

#define checkMemcpy(original, copy) \
    do { \
        if (sizeof array##original != sizeof array##copy) \
            return -original; \
        for (size_t i = 0; i < (sizeof array##original) / sizeof (*array##original); ++i, ++error_code) \
            if (array##original[i] != array##copy[i]) \
                return error_code; \
    } while (0)

#define checkMemset(number) \
    do { \
        for (size_t i = 0; i < (sizeof array##number) / sizeof (*array##number); ++i, ++error_code) \
            if (array##number[i] != 0) \
                return error_code; \
    } while (0)


int main(void) {
    size_t error_code = 1;

    createArray(unsigned char, 1);
    createArray(int, 2);
    createArray(long long, 3);

    emptyArray(unsigned char, 4);
    emptyArray(int, 5);
    emptyArray(long long, 6);

    doMemcpy(4, 1); doMemcpy(5, 2); doMemcpy(6, 3);
    checkMemcpy(1, 4); checkMemcpy(2, 5); checkMemcpy(3, 6);

    doMemset(4); doMemset(5); doMemset(6);
    checkMemset(4); checkMemset(5); checkMemset(6);

    doMemset(1); doMemset(2); doMemset(3);
    checkMemset(1); checkMemset(2); checkMemset(3);

    checkMemcpy(1, 4); checkMemcpy(2, 5); checkMemcpy(3, 6);

    return 0;
}
