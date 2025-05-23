#data_loader.py


import os
import numpy as np
import pandas as pd
import os
import torch
from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import StandardScaler
from backend.utils.timefeatures import time_features
from backend.utils.tools import convert_tsf_to_dataframe
import warnings
from pathlib import Path

warnings.filterwarnings('ignore')

class Dataset_ETT_hour(Dataset):
    def __init__(self, root_path, flag='train', size=None,
                 features='S', data_path='ETTh1.csv',
                 target='OT', scale=True, timeenc=0, freq='h',
                 percent=100, max_len=-1, train_all=False):
        # size [seq_len, label_len, pred_len]
        # info
        if size == None:
            self.seq_len = 24 * 4 * 4
            self.label_len = 24 * 4
            self.pred_len = 24 * 4
        else:
            self.seq_len = size[0]
            self.label_len = size[1]
            self.pred_len = size[2]
        # init
        assert flag in ['train', 'test', 'val']
        type_map = {'train': 0, 'val': 1, 'test': 2}
        self.set_type = type_map[flag]

        self.percent = percent
        self.features = features
        self.target = target
        self.scale = scale
        self.timeenc = timeenc
        self.freq = freq

        self.root_path = root_path
        self.data_path = data_path
        self.__read_data__()


        print("self.enc_in = {}".format(self.enc_in))
        print("self.data_x = {}".format(self.data_x.shape))
        self.tot_len = int(len(self.data_x) - self.seq_len - self.pred_len + 1)


    def __read_data__(self):
        self.scaler = StandardScaler()
       # self.enc_in = self.data_x.shape[-1]
        df_raw = pd.read_csv(os.path.join(self.root_path,
                                          self.data_path))


        # border1s = [int(x) if isinstance(x, (int, float)) and x.is_integer() else int(x) for x in [0, 12 * 30 * 24 - self.seq_len, 12 * 30 * 24 + 4 * 30 * 24 - self.seq_len]]
        # border2s = [int(x) if isinstance(x, (int, float)) and x.is_integer() else int(x) for x in [12 * 30 * 24, 12 * 30 * 24 + 4 * 30 * 24, 12 * 30 * 24 + 8 * 30 * 24]]


        border1s = [int(0), int(12 * 30 * 24 - self.seq_len), int(12 * 30 * 24 + 4 * 30 * 24 - self.seq_len)]
        border2s = [int(12 * 30 * 24), int(12 * 30 * 24 + 4 * 30 * 24), int(12 * 30 * 24 + 8 * 30 * 24)]
        border1 = int(border1s[self.set_type])  # Force int
        border2 = int(border2s[self.set_type])  # Force int

        if self.set_type == 0:
            border2 = int((border2 - self.seq_len) * self.percent // 100) + int(self.seq_len)

        if self.features == 'M' or self.features == 'MS':
            cols_data = df_raw.columns[1:]
            df_data = df_raw[cols_data]
        elif self.features == 'S':
            df_data = df_raw[[self.target]]

        if self.scale:
            train_data = df_data[border1s[0]:border2s[0]]
            self.scaler.fit(train_data.values)
            data = self.scaler.transform(df_data.values)
        else:
            data = df_data.values

        df_stamp = df_raw[['date']][border1:border2]
        df_stamp['date'] = pd.to_datetime(df_stamp.date)
        if self.timeenc == 0:
            df_stamp['month'] = df_stamp.date.apply(lambda row: row.month, 1)
            df_stamp['day'] = df_stamp.date.apply(lambda row: row.day, 1)
            df_stamp['weekday'] = df_stamp.date.apply(lambda row: row.weekday(), 1)
            df_stamp['hour'] = df_stamp.date.apply(lambda row: row.hour, 1)
            data_stamp = df_stamp.drop(['date'], 1).values
        elif self.timeenc == 1:
            data_stamp = time_features(pd.to_datetime(df_stamp['date'].values), freq=self.freq)
            data_stamp = data_stamp.transpose(1, 0)

        self.data_x = data[border1:border2]
        self.data_y = data[border1:border2]
        self.data_stamp = data_stamp
        self.enc_in = self.data_x.shape[-1]


    def __getitem__(self, index):
        index = int(index)
        print(f"Index type: {type(index)}")  # Should be int
        print(f"tot_len type: {type(self.tot_len)}")  # Should be int
        feat_id = int(index // self.tot_len)
        s_begin = int(index % self.tot_len)

        s_end = int(s_begin + self.seq_len)
        r_begin = int(s_end - self.label_len)
        r_end = int(r_begin + self.label_len + self.pred_len)
        # seq_x = self.data_x[s_begin:s_end, feat_id:feat_id+1]
        # seq_y = self.data_y[r_begin:r_end, feat_id:feat_id+1]
        # seq_x_mark = self.data_stamp[s_begin:s_end]
        # seq_y_mark = self.data_stamp[r_begin:r_end]
        seq_x = self.data_x[int(s_begin):int(s_end), int(feat_id):int(feat_id+1)]
        seq_y = self.data_y[int(r_begin):int(r_end), int(feat_id):int(feat_id+1)]
        seq_x_mark = self.data_stamp[int(s_begin):int(s_end)]
        seq_y_mark = self.data_stamp[int(r_begin):int(r_end)]

        return seq_x, seq_y, seq_x_mark, seq_y_mark

    def __len__(self):
        return int((len(self.data_x) - self.seq_len - self.pred_len + 1) * self.enc_in)

    def inverse_transform(self, data):
        return self.scaler.inverse_transform(data)

class Dataset_ETT_minute(Dataset):
    def __init__(self, root_path, flag='train', size=None,
                 features='S', data_path='ETTm1.csv',
                 target='OT', scale=True, timeenc=0, freq='t',
                 percent=100, max_len=-1, train_all=False):
        # size [seq_len, label_len, pred_len]
        # info
        if size == None:
            self.seq_len = 24 * 4 * 4
            self.label_len = 24 * 4
            self.pred_len = 24 * 4
        else:
            self.seq_len = size[0]
            self.label_len = size[1]
            self.pred_len = size[2]
        # init
        assert flag in ['train', 'test', 'val']
        type_map = {'train': 0, 'val': 1, 'test': 2}
        self.set_type = type_map[flag]

        self.features = features
        self.target = target
        self.scale = scale
        self.timeenc = timeenc
        self.freq = freq
        self.percent = percent

        self.root_path = root_path
        self.data_path = data_path
        self.__read_data__()

        self.tot_len = int(len(self.data_x) - self.seq_len - self.pred_len + 1)

    def __read_data__(self):
        self.scaler = StandardScaler()

        df_raw = pd.read_csv(os.path.join(self.root_path,
                                          self.data_path))

        border1s = [int(0), int(12 * 30 * 24 * 4 - self.seq_len), int(12 * 30 * 24 * 4 + 4 * 30 * 24 * 4 - self.seq_len)]
        border2s = [int(12 * 30 * 24 * 4), int(12 * 30 * 24 * 4 + 4 * 30 * 24 * 4), int(12 * 30 * 24 * 4 + 8 * 30 * 24 * 4)]
        border1 = int(border1s[self.set_type])  # Force int
        border2 = int(border2s[self.set_type])  # Force int
        if self.set_type == 0:
            border2 = int((border2 - self.seq_len) * self.percent // 100) + int(self.seq_len)

        if self.features == 'M' or self.features == 'MS':
            cols_data = df_raw.columns[1:]
            df_data = df_raw[cols_data]
        elif self.features == 'S':
            df_data = df_raw[[self.target]]

        if self.scale:
            train_data = df_data[border1s[0]:border2s[0]]
            self.scaler.fit(train_data.values)
            data = self.scaler.transform(df_data.values)
        else:
            data = df_data.values

        df_stamp = df_raw[['date']][border1:border2]
        df_stamp['date'] = pd.to_datetime(df_stamp.date)
        if self.timeenc == 0:
            df_stamp['month'] = df_stamp.date.apply(lambda row: row.month, 1)
            df_stamp['day'] = df_stamp.date.apply(lambda row: row.day, 1)
            df_stamp['weekday'] = df_stamp.date.apply(lambda row: row.weekday(), 1)
            df_stamp['hour'] = df_stamp.date.apply(lambda row: row.hour, 1)
            df_stamp['minute'] = df_stamp.date.apply(lambda row: row.minute, 1)
            df_stamp['minute'] = df_stamp.minute.map(lambda x: x // 15)
            data_stamp = df_stamp.drop(['date'], 1).values
        elif self.timeenc == 1:
            data_stamp = time_features(pd.to_datetime(df_stamp['date'].values), freq=self.freq)
            data_stamp = data_stamp.transpose(1, 0)

        self.data_x = data[border1:border2]
        self.data_y = data[border1:border2]
        self.enc_in = self.data_x.shape[-1]

        self.data_stamp = data_stamp
        self.enc_in = self.data_x.shape[-1]

    def __getitem__(self, index):
        index = int(index)
        feat_id = int(index // self.tot_len)
        s_begin = int(index % self.tot_len)

        s_end = int(s_begin + self.seq_len)
        r_begin = int(s_end - self.label_len)
        r_end = int(r_begin + self.label_len + self.pred_len)
        # seq_x = self.data_x[s_begin:s_end, feat_id:feat_id+1]
        # seq_y = self.data_y[r_begin:r_end, feat_id:feat_id+1]
        # seq_x_mark = self.data_stamp[s_begin:s_end]
        # seq_y_mark = self.data_stamp[r_begin:r_end]
        seq_x = self.data_x[int(s_begin):int(s_end), int(feat_id):int(feat_id+1)]
        seq_y = self.data_y[int(r_begin):int(r_end), int(feat_id):int(feat_id+1)]
        seq_x_mark = self.data_stamp[int(s_begin):int(s_end)]
        seq_y_mark = self.data_stamp[int(r_begin):int(r_end)]

        return seq_x, seq_y, seq_x_mark, seq_y_mark

    def __len__(self):
        return int((len(self.data_x) - self.seq_len - self.pred_len + 1) * self.enc_in)

    def inverse_transform(self, data):
        return self.scaler.inverse_transform(data)

class Dataset_Custom(Dataset):
    def __init__(self, root_path, flag='train', size=None,
                 features='S', data_path='ETTh1.csv',
                 target='OT', scale=True, timeenc=0, freq='h',
                 percent=10, max_len=-1, train_all=False):
        # size [seq_len, label_len, pred_len]
        # info
        if size == None:
            self.seq_len = 24 * 4 * 4
            self.label_len = 24 * 4
            self.pred_len = 24 * 4
        else:
            self.seq_len = size[0]
            self.label_len = size[1]
            self.pred_len = size[2]
        # init
        assert flag in ['train', 'test', 'val']
        type_map = {'train': 0, 'val': 1, 'test': 2}
        self.set_type = type_map[flag]

        self.features = features
        self.target = target
        self.scale = scale
        self.timeenc = timeenc
        self.freq = freq
        self.percent = percent

        self.root_path = root_path
        self.data_path = data_path
        self.__read_data__()

       # self.enc_in = self.data_x.shape[-1]
        self.tot_len = int(len(self.data_x) - self.seq_len - self.pred_len + 1)





    def __read_data__(self):
        self.scaler = StandardScaler()
         # This sets enc_in automatically
        full_path = os.path.join(self.root_path, self.data_path)
        df_raw = pd.read_csv(full_path)


        '''
        df_raw.columns: ['date', ...(other features), target feature]
        '''
        cols = list(df_raw.columns)
        cols.remove(self.target)
        cols.remove('date')
        df_raw = df_raw[['date'] + cols + [self.target]]
        # print(cols)
        num_train = int(len(df_raw) * 0.7)
        num_test = int(len(df_raw) * 0.2)
        num_vali = int(len(df_raw) - num_train - num_test)
       # border1s = [0, num_train - self.seq_len, len(df_raw) - num_test - self.seq_len]
        border1s = [int(0), int(num_train - self.seq_len), int(len(df_raw) - num_test - self.seq_len)]
        border2s = [int(num_train), int(num_train + num_vali), int(len(df_raw))]
        border1 = int(border1s[self.set_type])  # Force int
        border2 = int(border2s[self.set_type])  # Force int

        if self.set_type == 0:
            border2 = int((border2 - self.seq_len) * self.percent // 100) + int(self.seq_len)  # Ensure all terms are int

        if self.features == 'M' or self.features == 'MS':
            cols_data = df_raw.columns[1:]
            df_data = df_raw[cols_data]
        elif self.features == 'S':
            df_data = df_raw[[self.target]]

        if self.scale:
            train_data = df_data[border1s[0]:border2s[0]]
            self.scaler.fit(train_data.values)
            data = self.scaler.transform(df_data.values)
        else:
            data = df_data.values

        df_stamp = df_raw[['date']][border1:border2]
        df_stamp['date'] = pd.to_datetime(df_stamp.date)
        if self.timeenc == 0:
            df_stamp['month'] = df_stamp.date.apply(lambda row: row.month, 1)
            df_stamp['day'] = df_stamp.date.apply(lambda row: row.day, 1)
            df_stamp['weekday'] = df_stamp.date.apply(lambda row: row.weekday(), 1)
            df_stamp['hour'] = df_stamp.date.apply(lambda row: row.hour, 1)
            data_stamp = df_stamp.drop(['date'], 1).values
        elif self.timeenc == 1:
            data_stamp = time_features(pd.to_datetime(df_stamp['date'].values), freq=self.freq)
            data_stamp = data_stamp.transpose(1, 0)

        self.data_x = data[border1:border2]
        self.data_y = data[border1:border2]
        self.data_stamp = data_stamp
        self.enc_in = self.data_x.shape[-1]



    def __getitem__(self, index):
        index = int(index)
        feat_id = int(index // self.tot_len)
        s_begin = int(index % self.tot_len)

        s_end = int(s_begin + self.seq_len)
        r_begin = int(s_end - self.label_len)
        r_end = int(r_begin + self.label_len + self.pred_len)
        # seq_x = self.data_x[s_begin:s_end, feat_id:feat_id+1]
        # seq_y = self.data_y[r_begin:r_end, feat_id:feat_id+1]
        # seq_x_mark = self.data_stamp[s_begin:s_end]
        # seq_y_mark = self.data_stamp[r_begin:r_end]
         # Force all slice operations to use integers
        seq_x = self.data_x[int(s_begin):int(s_end), int(feat_id):int(feat_id+1)]
        seq_y = self.data_y[int(r_begin):int(r_end), int(feat_id):int(feat_id+1)]
        seq_x_mark = self.data_stamp[int(s_begin):int(s_end)]
        seq_y_mark = self.data_stamp[int(r_begin):int(r_end)]

        return seq_x, seq_y, seq_x_mark, seq_y_mark

    def __len__(self):
        return int((len(self.data_x) - self.seq_len - self.pred_len + 1) * self.enc_in)

    def inverse_transform(self, data):
        return self.scaler.inverse_transform(data)


class Dataset_Pred(Dataset):
    def __init__(self, root_path, flag='pred', size=None,
                 features='S', data_path='ETTh1.csv',
                 target='OT', scale=True, inverse=False, timeenc=0, freq='15min', cols=None,
                 percent=None, train_all=False):
        # size [seq_len, label_len, pred_len]
        # info
        if size == None:
            self.seq_len = 24 * 4 * 4
            self.label_len = 24 * 4
            self.pred_len = 24 * 4
        else:
            self.seq_len = size[0]
            self.label_len = size[1]
            self.pred_len = size[2]
        # init
        assert flag in ['pred']

        self.features = features
        self.target = target
        self.scale = scale
        self.inverse = inverse
        self.timeenc = timeenc
        self.freq = freq
        self.cols = cols
        self.root_path = root_path
        self.data_path = data_path
        self.__read_data__()

    def __read_data__(self):
        self.scaler = StandardScaler()

        df_raw = pd.read_csv(os.path.join(self.root_path,
                                          self.data_path))
        '''
        df_raw.columns: ['date', ...(other features), target feature]
        '''
        if self.cols:
            cols = self.cols.copy()
            cols.remove(self.target)
        else:
            cols = list(df_raw.columns)
            cols.remove(self.target)
            cols.remove('date')
        df_raw = df_raw[['date'] + cols + [self.target]]
        border1 = len(df_raw) - self.seq_len
        border2 = len(df_raw)

        if self.features == 'M' or self.features == 'MS':
            cols_data = df_raw.columns[1:]
            df_data = df_raw[cols_data]
        elif self.features == 'S':
            df_data = df_raw[[self.target]]

        if self.scale:
            self.scaler.fit(df_data.values)
            data = self.scaler.transform(df_data.values)
        else:
            data = df_data.values

        tmp_stamp = df_raw[['date']][border1:border2]
        tmp_stamp['date'] = pd.to_datetime(tmp_stamp.date)
        pred_dates = pd.date_range(tmp_stamp.date.values[-1], periods=self.pred_len + 1, freq=self.freq)

        df_stamp = pd.DataFrame(columns=['date'])
        df_stamp.date = list(tmp_stamp.date.values) + list(pred_dates[1:])
        if self.timeenc == 0:
            df_stamp['month'] = df_stamp.date.apply(lambda row: row.month, 1)
            df_stamp['day'] = df_stamp.date.apply(lambda row: row.day, 1)
            df_stamp['weekday'] = df_stamp.date.apply(lambda row: row.weekday(), 1)
            df_stamp['hour'] = df_stamp.date.apply(lambda row: row.hour, 1)
            df_stamp['minute'] = df_stamp.date.apply(lambda row: row.minute, 1)
            df_stamp['minute'] = df_stamp.minute.map(lambda x: x // 15)
            data_stamp = df_stamp.drop(['date'], 1).values
        elif self.timeenc == 1:
            data_stamp = time_features(pd.to_datetime(df_stamp['date'].values), freq=self.freq)
            data_stamp = data_stamp.transpose(1, 0)

        self.data_x = data[border1:border2]
        if self.inverse:
            self.data_y = df_data.values[border1:border2]
        else:
            self.data_y = data[border1:border2]
        self.data_stamp = data_stamp
        self.enc_in = self.data_x.shape[-1]


    def __getitem__(self, index):
        index = int(index)
        s_begin = int(index)
        s_end = int(s_begin + self.seq_len)
        r_begin = int(s_end - self.label_len)
        r_end = int(r_begin + self.label_len + self.pred_len)

        seq_x = self.data_x[s_begin:s_end]
        if self.inverse:
            seq_y = self.data_x[r_begin:r_begin + self.label_len]
        else:
            seq_y = self.data_y[r_begin:r_begin + self.label_len]
        seq_x_mark = self.data_stamp[s_begin:s_end]
        seq_y_mark = self.data_stamp[r_begin:r_end]

        return seq_x, seq_y, seq_x_mark, seq_y_mark

    def __len__(self):
        return int(len(self.data_x) - self.seq_len + 1)

    def inverse_transform(self, data):
        return self.scaler.inverse_transform(data)


class Dataset_TSF(Dataset):
    def __init__(self, root_path, flag='train', size=None,
                 features='S', data_path=None,
                 target='OT', scale=True, timeenc=0, freq='Daily',
                 percent=10, max_len=-1, train_all=False):

        self.train_all = train_all

        self.seq_len = size[0]
        self.pred_len = size[2]
        type_map = {'train': 0, 'val': 1, 'test': 2}
        self.set_type = type_map[flag]

        self.percent = percent
        self.max_len = max_len
        if self.max_len == -1:
            self.max_len = 1e8

        self.root_path = root_path
        self.data_path = data_path
        self.timeseries = self.__read_data__()


    def __read_data__(self):
        df, frequency, forecast_horizon, contain_missing_values, contain_equal_length = convert_tsf_to_dataframe(os.path.join(self.root_path,
                                                                                                                              self.data_path))
        self.freq = frequency
        def dropna(x):
            return x[~np.isnan(x)]
        timeseries = [dropna(ts).astype(np.float32) for ts in df.series_value]

        self.tot_len = 0
        self.len_seq = []
        self.seq_id = []
        self.enc_in = self.data_x.shape[-1]
        for i in range(len(timeseries)):
            res_len = max(self.pred_len + self.seq_len - timeseries[i].shape[0], 0)
            pad_zeros = np.zeros(res_len)
            timeseries[i] = np.hstack([pad_zeros, timeseries[i]])

            _len = timeseries[i].shape[0]
            train_len = _len-self.pred_len
            if self.train_all:
                border1s = [int(0),         int( 0),          int(train_len-self.seq_len)]
                border2s = [int(train_len),  int(train_len),  int(_len)]
            else:
                border1s = [int(0),                          int(train_len - self.seq_len - self.pred_len), int(train_len-self.seq_len)]
                border2s = [int(train_len - self.pred_len),  int(train_len),                                int(_len)]
            border2s[0] = int((border2s[0] - self.seq_len) * self.percent // 100) + int(self.seq_len)  # Force int
            # print("_len = {}".format(_len))

            curr_len = border2s[self.set_type] - max(border1s[self.set_type], 0) - self.pred_len - self.seq_len + 1
            curr_len = max(0, curr_len)

            self.len_seq.append(np.zeros(curr_len) + self.tot_len)
            self.seq_id.append(np.zeros(curr_len) + i)
            self.tot_len += curr_len

        self.len_seq = np.hstack(self.len_seq)
        self.seq_id = np.hstack(self.seq_id)

        return timeseries

    def __getitem__(self, index):
        index = int(index)
        len_seq = int(self.len_seq[index])
        seq_id = int(self.seq_id[index])
        index = index - int(len_seq)

        _len = self.timeseries[seq_id].shape[0]
        train_len = _len - self.pred_len
        if self.train_all:
            border1s = [0,          0,          train_len-self.seq_len]
            border2s = [train_len,  train_len,  _len]
        else:
            border1s = [0,                          train_len - self.seq_len - self.pred_len, train_len-self.seq_len]
            border2s = [train_len - self.pred_len,  train_len,                                _len]
        border2s[0] = (border2s[0] - self.seq_len) * self.percent // 100 + self.seq_len

        s_begin = int(index + border1s[self.set_type])
        s_end = int(s_begin + self.seq_len)
        r_begin = s_end
        r_end = int(r_begin + self.pred_len)
        if self.set_type == 2:
            s_end = -self.pred_len

        data_x = self.timeseries[seq_id][s_begin:s_end]
        data_y = self.timeseries[seq_id][r_begin:r_end]
        data_x = np.expand_dims(data_x, axis=-1)
        data_y = np.expand_dims(data_y, axis=-1)

        # if self.set_type == 2:
        #     print("data_x.shape = {}, data_y.shape = {}".format(data_x.shape, data_y.shape))

        return data_x, data_y, data_x, data_y

    def __len__(self):
        if self.set_type == 0:
            # return self.tot_len
            return min(self.max_len, self.tot_len)
        else:
            return self.tot_len
