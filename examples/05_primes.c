// 示例: 寻找素数
int is_prime(int n) {
    if (n <= 1) {
        return 0; // false
    }
    for (int i = 2; i < n; ++i) {
        if (n % i == 0) {
            return 0; // false
        }
    }
    return 1; // true
}

int main() {
    int limit = 20;
    int count = 0;
    
    for (int num = 2; num <= limit; ++num) {
        if (is_prime(num)) {
            count = count + 1;
        }
    }
    
    return count;
}
