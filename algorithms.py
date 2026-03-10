from visualizer import AlgorithmVisualizer
import bisect
import time

def bubble_sort(data):
    """
    A clean implementation of bubble sort that can be visualized.
    """
    viz = AlgorithmVisualizer(
        title="Bubble Sort",
        description="'i' is the outer loop index.\n'j' is the inner loop index, comparing adjacent elements."
    )
    arr = list(data)
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            pointers = {'i': i, 'j': j}
            viz.capture(arr, pointers)
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                pointers['j'] = j + 1
                viz.capture(arr, pointers)
    viz.capture(arr, final=True)
    print("Bubble sort complete!")

def merge_sort(data):
    """
    Sets up and starts the merge sort visualization.
    """
    viz = AlgorithmVisualizer(
        title="Merge Sort",
        description="Recursively splitting the array, then merging sorted sub-arrays.",
        speed=0.8
    )
    arr = list(data)
    _merge_sort_recursive(arr, viz, 0, len(arr) - 1)
    viz.capture(arr, final=True)
    print("Merge sort complete!")

def _merge_sort_recursive(arr, viz, left, right):
    if left < right:
        mid = (left + right) // 2
        _merge_sort_recursive(arr, viz, left, mid)
        _merge_sort_recursive(arr, viz, mid + 1, right)
        _merge(arr, viz, left, mid, right)

def _merge(arr, viz, left, mid, right):
    left_half = arr[left : mid + 1]
    right_half = arr[mid + 1 : right + 1]
    i, j, k = 0, 0, left
    sub_arrays = {"Left": left_half, "Right": right_half}
    while i < len(left_half) and j < len(right_half):
        highlights = {'main': k, 'sub': [i, j]}
        viz.capture(arr, pointers={'k': k}, sub_arrays=sub_arrays, highlights=highlights)
        if left_half[i] <= right_half[j]:
            arr[k] = left_half[i]
            i += 1
        else:
            arr[k] = right_half[j]
            j += 1
        k += 1
    while i < len(left_half):
        highlights = {'main': k, 'sub': [i, -1]}
        viz.capture(arr, pointers={'k': k}, sub_arrays=sub_arrays, highlights=highlights)
        arr[k] = left_half[i]
        i += 1
        k += 1
    while j < len(right_half):
        highlights = {'main': k, 'sub': [-1, j]}
        viz.capture(arr, pointers={'k': k}, sub_arrays=sub_arrays, highlights=highlights)
        arr[k] = right_half[j]
        j += 1
        k += 1

def find_pair_sum(data, target):
    """
    Visualizes the two-pointer algorithm to find a pair that sums to a target.
    Assumes the input array 'data' is sorted.
    """
    description_base = (
        f"Searching for a pair that sums to {target}.\n"
        "'L' is the left pointer, 'R' is the right pointer."
    )
    viz = AlgorithmVisualizer(
        title="Two-Pointer: Find Pair Sum",
        description=description_base,
        speed=1.5
    )
    arr = list(data)
    left, right = 0, len(arr) - 1
    found = False
    while left < right:
        current_sum = arr[left] + arr[right]
        pointers = {'L': left, 'R': right}
        viz.description = (
            f"{description_base}\n"
            f"L ({arr[left]}) + R ({arr[right]}) = {current_sum}"
        )
        viz.capture(arr, pointers)
        if current_sum == target:
            viz.description = f"Found! {arr[left]} + {arr[right]} = {target}"
            viz.capture(arr, pointers, final=True)
            print(f"Pair found: ({arr[left]}, {arr[right]})")
            found = True
            break
        elif current_sum < target:
            left += 1
        else:
            right -= 1
    if not found:
        viz.description = f"No pair found that sums to {target}."
        viz.capture(arr, {}, final=True)
        print("No pair found.")

def lis_visualized(nums):
    """
    Visualizes the O(n log n) solution for Longest Increasing Subsequence.
    """
    viz = AlgorithmVisualizer(
        title="Longest Increasing Subsequence (LIS)",
        speed=2.0
    )
    
    tails = []
    
    for i, num in enumerate(nums):
        description = (
            f"Processing num = {num}.\n"
            f"'tails' stores the smallest tail of all increasing subsequences."
        )
        viz.capture(
            array=nums,
            pointers={'num': i},
            lis_frame_data={'tails': list(tails), 'action': description}
        )
        time.sleep(viz.speed)

        idx = bisect.bisect_left(tails, num)
        
        if idx == len(tails):
            action_desc = f"'{num}' is > all tails. Extending subsequence."
            tails.append(num)
            
            viz.capture(
                array=nums,
                pointers={'num': i},
                lis_frame_data={
                    'tails': list(tails), 
                    'action': action_desc,
                    'highlight_idx': idx
                }
            )

        else:
            original_tail = tails[idx]
            tails[idx] = num
            
            viz.capture(
                array=nums,
                pointers={'num': i},
                lis_frame_data={
                    'tails': list(tails),
                    'action': f"'{num}' replaces '{original_tail}' to create a better base.",
                    'highlight_idx': idx
                }
            )
        time.sleep(viz.speed)

    final_desc = (
        f"Finished processing. The length of 'tails' is the LIS length.\n"
        f"LIS Length = {len(tails)}"
    )
    viz.capture(
        array=nums,
        lis_frame_data={'tails': list(tails), 'action': final_desc},
        final=True
    )
    print(f"The length of the Longest Increasing Subsequence is: {len(tails)}")

if __name__ == "__main__":
    nums = [10, 9, 2, 5, 3, 7, 101, 18]
    lis_visualized(nums)
