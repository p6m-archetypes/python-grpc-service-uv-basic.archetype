"""Performance benchmarking script for the Example Service gRPC API."""

import asyncio
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import List, Optional

import grpc
import click
from {{ prefix_name }}_{{ suffix_name }}_proto.src.{{ org_name }}.{{ solution_name }}.{{ prefix_name }}.{{ suffix_name }}.grpc import (
    {{ prefix_name }}_{{ suffix_name }}_pb2,
    {{ prefix_name }}_{{ suffix_name }}_pb2_grpc,
)


@dataclass
class BenchmarkResult:
    """Results from a benchmark run."""
    
    operation: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_time_seconds: float
    requests_per_second: float
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    min_latency_ms: float
    max_latency_ms: float


class GrpcBenchmark:
    """gRPC service benchmark runner."""
    
    def __init__(self, server_address: str = "localhost:9010"):
        self.server_address = server_address
        self.channel = None
        self.stub = None
    
    async def setup(self) -> None:
        """Set up gRPC connection."""
        self.channel = grpc.aio.insecure_channel(self.server_address)
        self.stub = {{ prefix_name }}_{{ suffix_name }}_pb2_grpc.{{ PrefixName }}{{ SuffixName }}Stub(self.channel)
        
        # Wait for connection
        await grpc.aio.channel_ready_future(self.channel)
        click.echo(f"Connected to gRPC server at {self.server_address}")
    
    async def teardown(self) -> None:
        """Clean up gRPC connection."""
        if self.channel:
            await self.channel.close()
    
    async def create_example_request(self, index: int) -> tuple[float, bool]:
        """Make a single CreateExample request and measure latency."""
        start_time = time.perf_counter()
        
        try:
            request = {{ prefix_name }}_{{ suffix_name }}_pb2.Create{{ PrefixName }}Request(
                {{ prefix_name }}={{ prefix_name }}_{{ suffix_name }}_pb2.{{ PrefixName }}(
                    name=f"benchmark-{{ prefix-name }}-{index}",
                    description=f"Benchmark test {{ prefix-name }} {index}"
                )
            )
            
            response = await self.stub.Create{{ PrefixName }}(request)
            end_time = time.perf_counter()
            
            return (end_time - start_time) * 1000, True  # Convert to milliseconds
            
        except Exception as e:
            end_time = time.perf_counter()
            click.echo(f"Request {index} failed: {e}", err=True)
            return (end_time - start_time) * 1000, False
    
    async def get_example_request(self, example_id: str) -> tuple[float, bool]:
        """Make a single GetExample request and measure latency."""
        start_time = time.perf_counter()
        
        try:
            request = {{ prefix_name }}_{{ suffix_name }}_pb2.Get{{ PrefixName }}Request(id=example_id)
            response = await self.stub.Get{{ PrefixName }}(request)
            end_time = time.perf_counter()
            
            return (end_time - start_time) * 1000, True
            
        except Exception as e:
            end_time = time.perf_counter()
            return (end_time - start_time) * 1000, False
    
    async def list_examples_request(self) -> tuple[float, bool]:
        """Make a single ListExamples request and measure latency."""
        start_time = time.perf_counter()
        
        try:
            request = {{ prefix_name }}_{{ suffix_name }}_pb2.Get{{ PrefixName }}sRequest(
                page_size=50,
                start_page=0
            )
            response = await self.stub.Get{{ PrefixName }}s(request)
            end_time = time.perf_counter()
            
            return (end_time - start_time) * 1000, True
            
        except Exception as e:
            end_time = time.perf_counter()
            return (end_time - start_time) * 1000, False
    
    async def run_concurrent_benchmark(
        self,
        operation: str,
        num_requests: int,
        concurrency: int
    ) -> BenchmarkResult:
        """Run a concurrent benchmark for the specified operation."""
        click.echo(f"Running {operation} benchmark: {num_requests} requests, {concurrency} concurrent")
        
        # Prepare tasks based on operation
        if operation == "create":
            tasks = [
                self.create_example_request(i)
                for i in range(num_requests)
            ]
        elif operation == "list":
            tasks = [
                self.list_examples_request()
                for i in range(num_requests)
            ]
        else:
            raise ValueError(f"Unknown operation: {operation}")
        
        # Run benchmark
        start_time = time.perf_counter()
        
        # Use semaphore to limit concurrency
        semaphore = asyncio.Semaphore(concurrency)
        
        async def bounded_task(task):
            async with semaphore:
                return await task
        
        results = await asyncio.gather(*[bounded_task(task) for task in tasks])
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        # Process results
        latencies = [result[0] for result in results]
        successes = [result[1] for result in results]
        
        successful_requests = sum(successes)
        failed_requests = len(successes) - successful_requests
        
        # Calculate statistics
        latencies_sorted = sorted(latencies)
        
        return BenchmarkResult(
            operation=operation,
            total_requests=num_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            total_time_seconds=total_time,
            requests_per_second=num_requests / total_time,
            avg_latency_ms=statistics.mean(latencies),
            p50_latency_ms=latencies_sorted[int(len(latencies_sorted) * 0.5)],
            p95_latency_ms=latencies_sorted[int(len(latencies_sorted) * 0.95)],
            p99_latency_ms=latencies_sorted[int(len(latencies_sorted) * 0.99)],
            min_latency_ms=min(latencies),
            max_latency_ms=max(latencies),
        )


def print_benchmark_result(result: BenchmarkResult) -> None:
    """Print benchmark results in a formatted table."""
    click.echo("\n" + "="*80)
    click.echo(f"BENCHMARK RESULTS - {result.operation.upper()} OPERATION")
    click.echo("="*80)
    click.echo(f"Total Requests:       {result.total_requests:>10}")
    click.echo(f"Successful Requests:  {result.successful_requests:>10}")
    click.echo(f"Failed Requests:      {result.failed_requests:>10}")
    click.echo(f"Success Rate:         {result.successful_requests/result.total_requests*100:>9.1f}%")
    click.echo("-"*80)
    click.echo(f"Total Time:           {result.total_time_seconds:>9.3f}s")
    click.echo(f"Requests/Second:      {result.requests_per_second:>9.1f}")
    click.echo("-"*80)
    click.echo(f"Average Latency:      {result.avg_latency_ms:>9.2f}ms")
    click.echo(f"P50 Latency:          {result.p50_latency_ms:>9.2f}ms")
    click.echo(f"P95 Latency:          {result.p95_latency_ms:>9.2f}ms")
    click.echo(f"P99 Latency:          {result.p99_latency_ms:>9.2f}ms")
    click.echo(f"Min Latency:          {result.min_latency_ms:>9.2f}ms")
    click.echo(f"Max Latency:          {result.max_latency_ms:>9.2f}ms")
    click.echo("="*80)


@click.group()
def cli():
    """gRPC service performance benchmarking tools."""
    pass


@cli.command()
@click.option("--server", "-s", default="localhost:9010", help="gRPC server address")
@click.option("--requests", "-n", default=1000, help="Total number of requests")
@click.option("--concurrency", "-c", default=10, help="Number of concurrent requests")
@click.option("--operation", "-o", 
              type=click.Choice(["create", "list", "all"]), 
              default="all", 
              help="Operation to benchmark")
def benchmark(server: str, requests: int, concurrency: int, operation: str):
    """Run performance benchmark against the gRPC service."""
    
    async def run_benchmarks():
        benchmark_runner = GrpcBenchmark(server)
        
        try:
            await benchmark_runner.setup()
            
            operations = ["create", "list"] if operation == "all" else [operation]
            results = []
            
            for op in operations:
                click.echo(f"\nStarting {op} benchmark...")
                result = await benchmark_runner.run_concurrent_benchmark(
                    op, requests, concurrency
                )
                results.append(result)
                print_benchmark_result(result)
            
            # Print summary if multiple operations
            if len(results) > 1:
                click.echo("\n" + "="*80)
                click.echo("SUMMARY")
                click.echo("="*80)
                for result in results:
                    click.echo(f"{result.operation.upper():>10}: "
                             f"{result.requests_per_second:>7.1f} req/s, "
                             f"{result.avg_latency_ms:>6.2f}ms avg")
                click.echo("="*80)
        
        finally:
            await benchmark_runner.teardown()
    
    asyncio.run(run_benchmarks())


@cli.command()
@click.option("--server", "-s", default="localhost:9010", help="gRPC server address")
@click.option("--duration", "-d", default=30, help="Test duration in seconds")
@click.option("--concurrency", "-c", default=10, help="Number of concurrent requests")
def load_test(server: str, duration: int, concurrency: int):
    """Run a continuous load test for the specified duration."""
    
    async def run_load_test():
        benchmark_runner = GrpcBenchmark(server)
        
        try:
            await benchmark_runner.setup()
            
            click.echo(f"Running load test for {duration} seconds with {concurrency} concurrent requests...")
            
            start_time = time.time()
            end_time = start_time + duration
            request_count = 0
            latencies = []
            errors = 0
            
            async def worker():
                nonlocal request_count, errors
                while time.time() < end_time:
                    latency, success = await benchmark_runner.create_example_request(request_count)
                    latencies.append(latency)
                    request_count += 1
                    if not success:
                        errors += 1
            
            # Start worker tasks
            tasks = [asyncio.create_task(worker()) for _ in range(concurrency)]
            
            # Wait for all tasks to complete
            await asyncio.gather(*tasks)
            
            # Calculate results
            actual_duration = time.time() - start_time
            rps = request_count / actual_duration
            avg_latency = statistics.mean(latencies) if latencies else 0
            
            click.echo(f"\nLoad Test Results:")
            click.echo(f"Duration: {actual_duration:.2f}s")
            click.echo(f"Total Requests: {request_count}")
            click.echo(f"Errors: {errors}")
            click.echo(f"Requests/Second: {rps:.2f}")
            click.echo(f"Average Latency: {avg_latency:.2f}ms")
            
        finally:
            await benchmark_runner.teardown()
    
    asyncio.run(run_load_test())


if __name__ == "__main__":
    cli()