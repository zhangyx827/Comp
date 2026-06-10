// 示例: 综合指针和数组
int main() {
    int arr[3];
    arr[0] = 100;
    arr[1] = 200;
    arr[2] = arr[0] + arr[1];

    int *ptr = &arr[0];
    int result = *ptr;
    return result;
}