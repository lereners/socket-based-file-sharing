import pandas as pd
import matplotlib.pyplot as plt

# read file then do the statistics before moving onto another file

def print_statistics(column, name, units):
    # prints the average and the first five values of the entered df column
    print(f"Average {name}: {round(column.mean(), 5)} {units}")
    print(f"---{name} Sample---")
    print(column.head(5))

def main():
    try:
        # SERVERSIDE
        # upload (maybe make into separate functions for each of these)
        file_data = pd.read_csv("server_root/file_data.csv")

        # trouble accessing columns
        upload_time = file_data["UploadTime"]
        file_size = file_data["FileSize"] / (1000000)
        file_data["SizeinMB"] = file_size
        # add a column to the dataframe with the upload rate in MB/s
        file_data["UploadRate"] = file_size / upload_time
        print("Server Side Statistics: ")
        print_statistics(file_data["UploadRate"], "Upload Rate", "MB/s")
        print_statistics(upload_time, "Upload Time", "s")

        # plot of upload time (y) vs. file size
        file_data.plot(x='SizeinMB', y='UploadTime', xlabel='Size (MB)', ylabel='Time (s)', kind='line')
        plt.title("Upload time (s) vs Size (MB)")
        plt.show()

        # 
        try:
            download_data = pd.read_csv("server_root/download_info.csv")
        except FileNotFoundError:
            print("Error: file not found.")
        except Exception as e:
            print("An unexpected error occured: {e}")

        try:
            response_time = pd.read_csv("server_root/response_times.csv")
        except FileNotFoundError:
            print("Error: file not found.")
        except Exception as e:
            print("An unexpected error occured: {e}")


    except FileNotFoundError:
        print("Error: file not found.")
    except Exception as e:
        print("An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()