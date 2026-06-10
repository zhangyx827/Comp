// 综合测试程序：排序算法
int max_value(int a, int b) {
    if (a > b) {
        return a;
    }
    return b;
}

int min_value(int a, int b) {
    if (a < b) {
        return a;
    }
    return b;
}

int abs_diff(int x, int y) {
    int diff = x - y;
    if (diff < 0) {
        return -diff;
    }
    return diff;
}

int sum_array(int arr[5]) {
    int total = 0;
    for (int i = 0; i < 5; i = i + 1) {
        total = total + arr[i];
    }
    return total;
}

int find_max(int arr[5]) {
    int max_val = arr[0];
    for (int i = 1; i < 5; i = i + 1) {
        max_val = max_value(max_val, arr[i]);
    }
    return max_val;
}

int main() {
    // 变量声明
    int a = 10, b = 20, c = 30;
    int x = 5, y = 15;

    // 算术运算
    int sum = a + b + c;
    int product = x * y;
    int diff = b - a;

    // 条件表达式
    int max_num = max_value(a, b);
    int min_num = min_value(b, c);
    int abs_val = abs_diff(x, y);

    // 数组操作
    int numbers[5];
    numbers[0] = 42;
    numbers[1] = 17;
    numbers[2] = 89;
    numbers[3] = 23;
    numbers[4] = 56;

    // 数组求和
    int total = sum_array(numbers);
    int maximum = find_max(numbers);

    // 指针操作
    int *ptr1 = &numbers[0];
    int *ptr2 = &numbers[2];
    int val1 = *ptr1;
    int val2 = *ptr2;

    // 复杂循环
    int count = 0;
    for (int i = 0; i < 3; i = i + 1) {
        for (int j = 0; j < 3; j = j + 1) {
            count = count + 1;
        }
    }

    // 嵌套条件
    int result = 0;
    if (sum > 50) {
        if (product > 50) {
            result = sum + product;
        } else {
            result = sum - product;
        }
    } else {
        if (maximum > 50) {
            result = total;
        } else {
            result = count;
        }
    }

    return result;
}
