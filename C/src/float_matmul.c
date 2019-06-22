#include "float_arrays.h"

void matmul(double dst[CR][CC], double A[AR][AC], double B[BR][BC]) {
    for (int i = 0; i < AR; i++) {
        for (int j = 0; j < BC; j++) {
            dst[i][j] = 0;
            for (int k = 0; k < AC; k++) {
                dst[i][j] += A[i][k] * B[k][j];
            }
        }
    }
    return;
}

int main() {
    double DST[CR][CC] = {{0}};

    matmul(DST, A, B);

    for (unsigned i = 0; i < CR; i++) {
        for (unsigned j = 0; j < CC; j++) {
            if (DST[i][j] != C[i][j])
                // the return value will be greater than 0
                return i + j + 1;
        }
    }

    return 0;
}
