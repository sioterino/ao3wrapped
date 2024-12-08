import pandas as pd
# just an auxiliar method to helpe formating the wrapped
# since it started to get crowd-y on the main .py file
class Auxiliar:
    # filters through the user.csv dataframe
    # since its structure is different from that of the work.csv
    # we have to use different functions for it to work
    def filter_df(df, filter: str):
        filtered_df = df.loc[df['filter'] == filter]
        filtered_df = filtered_df.reset_index(drop=True)
        filtered_df.drop(["Unnamed: 0", "filter"], axis=1, inplace=True)

        return filtered_df.values

    # finds the index of an element in side of a 2d array
    def index_of(arr: list, target: str) :
        for i in range(len(arr)):
            for j in range(len(arr[i])):
                if arr[i][j] == target:
                    return i, j
        return -1, -1

    # increments 1 in the j index bc im lazy af
    def amount_index(index):
        return index[0], index[1] + 1

    # prints authors pretilly
    def authors_prettily(authors):
        if authors:
            match len(authors):
                case 1: return str(authors[0])
                case 2: return f"{str(authors[0])} and {str(authors[1])}"
                case _: return f"{', '.join(authors[:-1])} and {authors[-1]}"
        else: return "Anonymous Author"

    # get element from i,dex
    def get_efi(df, header: str, index: int):
        try:
            return eval(df[header].iloc[index])
        except:
            return df[header].iloc[index]

    # gets index of the biggest element in a column
    def idmax_of(df, header: str):
        return df[header].idxmax()

    def idmin_of(df, header: str):
        return df[header].idxmin()

    def mean_of(df, header):
        return df.describe().at["mean", header]

    def longest_str(arr):
        longest = arr[0][0]  # Start with the first string
        for i in range(1, len(arr)):  # Starting from index 1 to avoid comparing the same string
            if len(arr[i][0]) > len(longest):  # Compare string lengths
                longest = arr[i][0]  # Update longest if the current string is longer
        return longest

    def you_also(arr):
        print("\nYou also read this year:")
        counter = 1;
        for i in range(len(arr)):
            for j in range(len(arr[i]) - 1, 0, -1):
                print(f"  {counter}. ", end="")
                print(f"{arr[i][j -1]:>{len(Auxiliar.longest_str(arr)) + 2}} {arr[i][j]} times")
                counter += 1
                