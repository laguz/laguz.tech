import timeit
import datetime
import random

class DataGenerator:
    def __init__(self, size):
        self.data = [{'date': datetime.datetime.now(), 'pnl': random.random()} for _ in range(size)]

    def benchmark_for_loop(self):
        pnl_dates = []
        pnl_values = []
        for data in self.data:
            pnl_dates.append(data['date'].strftime('%Y-%m-%d'))
            pnl_values.append(data['pnl'])
        return pnl_dates, pnl_values

    def benchmark_list_comp(self):
        pnl_dates = [data['date'].strftime('%Y-%m-%d') for data in self.data]
        pnl_values = [data['pnl'] for data in self.data]
        return pnl_dates, pnl_values

    def benchmark_zip_list_comp(self):
        res = list(zip(*[(data['date'].strftime('%Y-%m-%d'), data['pnl']) for data in self.data]))
        if not res:
            return [], []
        pnl_dates, pnl_values = list(res[0]), list(res[1])
        return pnl_dates, pnl_values

if __name__ == '__main__':
    gen = DataGenerator(100)
    for_time = timeit.timeit(gen.benchmark_for_loop, number=10000)
    list_comp_time = timeit.timeit(gen.benchmark_list_comp, number=10000)
    zip_time = timeit.timeit(gen.benchmark_zip_list_comp, number=10000)
    print(f"For loop (N=100): {for_time:.5f}s")
    print(f"List comp (N=100): {list_comp_time:.5f}s")
    print(f"Zip List comp (N=100): {zip_time:.5f}s")

    gen = DataGenerator(1000)
    for_time = timeit.timeit(gen.benchmark_for_loop, number=1000)
    list_comp_time = timeit.timeit(gen.benchmark_list_comp, number=1000)
    zip_time = timeit.timeit(gen.benchmark_zip_list_comp, number=1000)
    print(f"For loop (N=1000): {for_time:.5f}s")
    print(f"List comp (N=1000): {list_comp_time:.5f}s")
    print(f"Zip List comp (N=1000): {zip_time:.5f}s")

    gen = DataGenerator(10000)
    for_time = timeit.timeit(gen.benchmark_for_loop, number=100)
    list_comp_time = timeit.timeit(gen.benchmark_list_comp, number=100)
    zip_time = timeit.timeit(gen.benchmark_zip_list_comp, number=100)
    print(f"For loop (N=10000): {for_time:.5f}s")
    print(f"List comp (N=10000): {list_comp_time:.5f}s")
    print(f"Zip List comp (N=10000): {zip_time:.5f}s")
