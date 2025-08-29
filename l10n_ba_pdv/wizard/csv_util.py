class CsvUtil:

    def _to_csv_2_dec(num):
        num = round(num, 2)
        return f"{num:.2f}"
