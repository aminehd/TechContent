"""
demo_solution.py  –  Example LeetCode-style solutions for testing the visualiser.

Run any of these:

  python -m viz_framework.run viz_framework/demo_solution.py two_sum "[2,7,11,15]" 9
  python -m viz_framework.run viz_framework/demo_solution.py binary_search "[1,3,5,7,9,11,13]" 7
  python -m viz_framework.run viz_framework/demo_solution.py merge_sorted_arrays "[1,3,5]" "[2,4,6]"
  python -m viz_framework.run viz_framework/demo_solution.py max_subarray "[-2,1,-3,4,-1,2,1,-5,4]"
  python -m viz_framework.run viz_framework/demo_solution.py container_with_most_water "[1,8,6,2,5,4,8,3,7]"

Or import and use the API directly:

  from viz_framework import trace_interactive
  from viz_framework.demo_solution import two_sum
  trace_interactive(two_sum, [2, 7, 11, 15], 9)
"""


# ---------------------------------------------------------------------------
# LC 1 – Two Sum  (two nested loops, two index pointers)
# ---------------------------------------------------------------------------

def two_sum(nums, target):
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []


# ---------------------------------------------------------------------------
# LC 704 – Binary Search  (classic lo/hi/mid pattern)
# ---------------------------------------------------------------------------

def binary_search(nums, target):
    lo, hi = 0, len(nums) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if nums[mid] == target:
            return mid
        elif nums[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1


# ---------------------------------------------------------------------------
# Merge two sorted arrays  (two pointer merge)
# ---------------------------------------------------------------------------

def merge_sorted_arrays(a, b):
    result = []
    i, j = 0, 0
    while i < len(a) and j < len(b):
        if a[i] <= b[j]:
            result.append(a[i])
            i += 1
        else:
            result.append(b[j])
            j += 1
    while i < len(a):
        result.append(a[i])
        i += 1
    while j < len(b):
        result.append(b[j])
        j += 1
    return result


# ---------------------------------------------------------------------------
# LC 53 – Maximum Subarray  (Kadane's algorithm, DP array)
# ---------------------------------------------------------------------------

def max_subarray(nums):
    dp = [0] * len(nums)
    dp[0] = nums[0]
    for i in range(1, len(nums)):
        dp[i] = max(nums[i], dp[i - 1] + nums[i])
    return max(dp)


# ---------------------------------------------------------------------------
# LC 11 – Container With Most Water  (two-pointer shrink)
# ---------------------------------------------------------------------------

def container_with_most_water(height):
    l, r = 0, len(height) - 1
    max_water = 0
    while l < r:
        water = min(height[l], height[r]) * (r - l)
        max_water = max(max_water, water)
        if height[l] < height[r]:
            l += 1
        else:
            r -= 1
    return max_water


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    assert two_sum([2, 7, 11, 15], 9) == [0, 1]
    assert binary_search([1, 3, 5, 7, 9], 7) == 3
    assert merge_sorted_arrays([1, 3, 5], [2, 4, 6]) == [1, 2, 3, 4, 5, 6]
    assert max_subarray([-2, 1, -3, 4, -1, 2, 1, -5, 4]) == 6
    assert container_with_most_water([1, 8, 6, 2, 5, 4, 8, 3, 7]) == 49
    print("All self-tests passed.")
