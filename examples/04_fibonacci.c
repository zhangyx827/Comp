// 示例: 斐波那契数列计算 (递归)
int fibonacci(int n) {
    if (n <= 1) {
        return n;
    }
    return fibonacci(n - 1) + fibonacci(n - 2);
}

int main() {
    int n = 10;
    int result = fibonacci(n);
    return result;
}
