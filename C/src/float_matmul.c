#define AR 4
#define AC 4
#define BR AC
#define BC 5
#define CR AR
#define CC BC

void matmul(double **dst, double **A, double **B) {
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
    double A[AR][AC] = {
        {1,2,3,4},
        {2,3,4,5},
        {3,4,5,6},
        {4,5,6,7}
    };
    double B[BR][BC] = {
        {0,1,2,3,4},
        {1,2,3,4,5},
        {2,3,4,5,6},
        {3,4,5,6,7}
    };

    double DST[CR][CC] = {{0}};

    static const double correct[CR][CC] = {
        {20.,  30.,  40.,  50.,  60.},
        {26.,  40.,  54.,  68.,  82.},
        {32.,  50.,  68.,  86., 104.},
        {38.,  60.,  82., 104., 126.}
    };

    matmul((double **)DST, (double **)A, (double **)B);

    for (unsigned i = 0; i < CR; i++) {
        for (unsigned j = 0; j < CC; j++) {
            if (DST[i][j] != correct[i][j])
                return i + j + 1;
        }
    }
    return 0;
}
