

def add_year_word(n: int) -> str:
    # Проверяем исключения (11-14 лет)
    if 11 <= n % 100 <= 14:
        return f"{n} лет"

    # Проверяем последнюю цифру
    last_digit = n % 10

    if last_digit == 1:
        return f"{n} год"
    elif 2 <= last_digit <= 4:
        return f"{n} года"
    else:
        return f"{n} лет"
