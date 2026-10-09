import csv
import random

# Generate a small sample of Google Cluster Trace 2011 (v2) task_usage events
def generate_sample(filename, num_records=1000):
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        # Times in microseconds since trace start
        # Let's generate records over a period of 1 hour (3600 seconds = 3600 * 1e6 us)
        for i in range(num_records):
            start_time = random.randint(0, 3500) * 1000000
            end_time = start_time + 300 * 1000000 # 5 minutes duration
            job_id = random.randint(1000, 1100)
            task_index = random.randint(0, 50)
            machine_id = random.randint(1, 100)
            
            # Simulate a workload pattern (e.g. higher CPU in the middle of the hour)
            time_normalized = start_time / (3600 * 1000000)
            base_cpu = 0.05 + 0.1 * time_normalized  # Base increasing
            if 0.4 < time_normalized < 0.6:
                base_cpu += 0.2  # Spike in the middle
                
            cpu_rate = max(0.001, min(1.0, random.gauss(base_cpu, 0.02)))
            canonical_memory_usage = max(0.001, min(1.0, random.gauss(0.02 + 0.05 * time_normalized, 0.01)))
            
            # Other fields can be zero or empty for our purposes, but let's put realistic zeroes
            row = [
                start_time, end_time, job_id, task_index, machine_id, 
                round(cpu_rate, 5), round(canonical_memory_usage, 5), 
                '', '', '', '', '', '', '', '', '', '', '', '', ''
            ]
            writer.writerow(row)

if __name__ == '__main__':
    generate_sample('data/raw/google_cluster_trace/sample_task_usage.csv')

