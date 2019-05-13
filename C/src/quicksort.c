// Original: https://gist.github.com/wtsnjp/53222131fd86824858fc0b37cd9db98a

/*
 *
 * compile: gcc quicksort.c
 * test: ./a.out
 *
 */

#include <stdio.h>

enum { SIZE = 30 };

void quicksort(int *target, int left, int right) {
  if(left >= right) return;
  int i = left, j = right;
  int tmp, pivot = target[i];
  for(;;) {
    while(target[i] < pivot) i++;
    while(pivot < target[j]) j--;
    if(i >= j) break;
    tmp = target[i]; target[i] = target[j]; target[j] = tmp;
    i++; j--;
  }
  quicksort(target, left, i-1);
  quicksort(target, j+1, right);
}

int main() {
  int i, array[SIZE] = { 18, 12, 8, 14, 13, 16, 29, 17, 5, 26, 11, 20, 3, 1, 7, 28, 4, 2, 15, 0, 9, 24, 27, 23, 21, 22, 10, 19, 25, 6 };

  quicksort(array, 0, SIZE-1);

  for(i=0; i<SIZE; i++)
    printf("%d,", array[i]);
  printf("\n");

  for (size_t i = 0; i < SIZE; ++i)
    if (array[i] != i)
        return i + 1;

  return 0;
}
