long long abs(const long long a) {
	return (a < 0)?(-a):a;
}

// raise 'a' to a non-negative power 'b'
long long pow(long long a, long long b) {
	if (b < 0)
		return -1;

	if (b == 0)
		return 1;

	char sign = a < 0;
	a = abs(a);

	// there's no support for multiplication yet, so...
	const long long a_orig = a;
	for (long long i = 0; i < b; i++)
		for (long long j = 0; j < a_orig; j++)
			a += a_orig;

	if (sign && (b & 1))
		a = -a;

	return a;
}

int main(void) {
	return pow(5, 4); // must be 625
}