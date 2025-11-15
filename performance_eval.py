import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# read file then do the statistics before moving onto another file

def print_statistics(column, name, units):
    # prints the average and the first five values of the entered df column
    print(f"Average {name}: {round(column.mean(), 5)} {units}")
    print(f"---{name} Sample---")
    print(column.head(5))

def main():
    try:
        # SERVERSIDE
        response_times = pd.read_csv("server_data/response_times.csv")
        print(response_times.head())
        print_statistics(response_times['ResponseTime'], "Response Time", "s")
        # response_times["Average"]

        num_rows = len(response_times)
        sum_download = 0
        num_download = 0
        sum_upload = 0
        num_upload = 0
        sum_delete = 0
        num_delete = 0

        # bar chart for response times
        for i in range(num_rows):
            label = response_times.loc[i, 'Command']
            value = response_times.loc[i, 'ResponseTime']
            if label == "download":
                sum_download += value
                num_download += 1
            elif label == "upload":
                sum_upload += value
                num_upload += 1
            elif label == "delete":
                sum_delete += value
                num_delete += 1
            else:
                print("Invalid key")

        # print(f'dl: {sum_download}, {sum_upload}, {sum_delete}')
        # print(f"Averages: Delete {round(sum_download / num_download, 5)}s, Upload {round(sum_upload / num_upload, 5)}s, Delete: {round(sum_delete / num_delete, 5)}s")
       
        bu = 0
        print(f"Averages: Download {round(sum_download / num_download, 5) if num_download >= 1 else bu}s, Upload {round(sum_upload / num_upload, 5) if num_upload >= 1 else bu}s, Delete: {round(sum_delete / num_delete, 5)if num_delete >= 1 else bu}s")

        try:
             # upload (maybe make into separate functions for each of these)
            file_data = pd.read_csv("server_data/file_data.csv")

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

            print("done")

            try:
                download_data = pd.read_csv("server_data/download_info.csv")
                download_time = download_data["DownloadTime"]
                download_size = download_data["FileSize"] / (1000000)
                download_data["SizeinMB"] = download_size
                # add a column to the dataframe with the upload rate in MB/s
                download_data["DownloadRate"] = download_size / download_time
                print_statistics(download_data["DownloadRate"], "Download Rate", "MB/s")
                print_statistics(download_time, "Download Time", "s")

                download_data.plot(x='SizeinMB', y='DownloadTime', xlabel='Size (MB)', ylabel='Time (s)', kind='line')
                plt.title("Download time (s) vs Size (MB)")
                plt.show()

            
            except FileNotFoundError:
                print("Error: file not found.")
            except Exception as e:
                print("An unexpected error occured: {e}")

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