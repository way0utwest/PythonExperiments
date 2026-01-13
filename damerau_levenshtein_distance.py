def damerau_levenshtein_distance(s1, s2):
    """
    Calculate the Damerau-Levenshtein distance between two strings.
    
    This metric measures the minimum number of operations needed to transform
    one string into another, where operations include:
    - Insertion of a character
    - Deletion of a character
    - Substitution of a character
    - Transposition of two adjacent characters
    
    Args:
        s1: First string
        s2: Second string
    
    Returns:
        int: The Damerau-Levenshtein distance
    """
    len1, len2 = len(s1), len(s2)
    
    # Create a dictionary to store all unique characters
    da = {}
    
    # First row and column (represent adding all letters from other string)
    max_dist = len1 + len2
    H = {}  # Dictionary for dynamic programming
    H[-1, -1] = max_dist
    
    for i in range(0, len1 + 1):
        H[i, -1] = max_dist
        H[i, 0] = i
    for j in range(0, len2 + 1):
        H[-1, j] = max_dist
        H[0, j] = j
    
    for i in range(1, len1 + 1):
        db = 0
        for j in range(1, len2 + 1):
            k = da.get(s2[j-1], 0)
            l = db
            cost = 1
            if s1[i-1] == s2[j-1]:
                cost = 0
                db = j
            
            H[i, j] = min(
                H[i-1, j] + 1,      # deletion
                H[i, j-1] + 1,      # insertion
                H[i-1, j-1] + cost, # substitution
                H[k-1, l-1] + (i-k-1) + 1 + (j-l-1)  # transposition
            )
        
        da[s1[i-1]] = i
    
    return H[len1, len2]


# Example usage
if __name__ == "__main__":
    # Test cases
    test_pairs = [
        ("Steve", "Steven"),
        ("colour", "color"),
        ("whilst", "color"),
        ("book", "back"),
        ("hello", "helo"),
        ("", "abc"),
        ("abc", ""),
    ]
    
    print("Damerau-Levenshtein Distance Examples:")
    print("-" * 50)
    for s1, s2 in test_pairs:
        distance = damerau_levenshtein_distance(s1, s2)
        print(f'"{s1}" → "{s2}": {distance}')