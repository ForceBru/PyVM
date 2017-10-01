long long abs(const long long a) {
	if (a < 0)
        return -a;
    return a;
}

// raise 'a' to a non-negative power 'b'
long long pow(long long a, long long b) {
	if (b < 0)
		return -1;

	if (b == 0)
		return 1;

	int sign = 0;
    if (a < 0) sign = 1;
	a = abs(a);

	// there's no support for multiplication yet, so...
	const long long a_orig = a;
	for (long long i = 0; i < b; i++)
		for (long long j = 0; j < a_orig; j++)
			a += a_orig;

	if (sign && (b & 1))
		return -a;

	return a;
}

int main(void) {
	return pow(5, 4); // must be 625
}