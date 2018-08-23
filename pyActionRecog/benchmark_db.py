import glob
import fnmatch
import os
import random
from anet_db import ANetDB


def parse_directory(path, rgb_prefix='img_', flow_x_prefix='flow_x_', flow_y_prefix='flow_y_'):
    """
    Parse directories holding extracted frames from standard benchmarks
    """
    print 'parse frames under folder {}'.format(path)
    frame_folders = glob.glob(os.path.join(path, '*'))

    def count_files(directory, prefix_list):
        lst = os.listdir(directory)
        cnt_list = [len(fnmatch.filter(lst, x+'*')) for x in prefix_list]
        return cnt_list

    # check RGB
    rgb_counts = {}
    flow_counts = {}
    dir_dict = {}
    for i,f in enumerate(frame_folders):
        all_cnt = count_files(f, (rgb_prefix, flow_x_prefix, flow_y_prefix))
        k = f.split('/')[-1]
        rgb_counts[k] = all_cnt[0]
        dir_dict[k] = f

        x_cnt = all_cnt[1]
        y_cnt = all_cnt[2]
        if x_cnt != y_cnt:
            raise ValueError('x and y direction have different number of flow images. video: '+f)
        flow_counts[k] = x_cnt
        if i % 200 == 0:
            print '{} videos parsed'.format(i)

    print 'frame folder analysis done'
    return dir_dict, rgb_counts, flow_counts


def build_split_list(split_tuple, frame_info, split_idx, shuffle=False):
    split = split_tuple[split_idx] #split_idx = 3 split_tuple= [(names,labels),(names,labels),(names,labels)]

    def build_set_list(set_list):
        rgb_list, flow_list = list(), list()
        for item in set_list:
            frame_dir = frame_info[0][item[0]] #frame_info[0] = dir_dict: {'Return_of_the_King_11_smoke_h_nm_np1_fr_med_2': '/home/LX/hmdb_handup/Return_of_the_King_11_smoke_h_nm_np1_fr_med_2'}
            rgb_cnt = frame_info[1][item[0]] #frame_info[1] = rgb_counts: {'Bubble_Blowing_Bubble_Gum_chew_h_nm_np1_fr_bad_2': 113}
            flow_cnt = frame_info[2][item[0]] #frame_info[2] = flow_counts: {'Return_of_the_King_11_smoke_h_nm_np1_fr_med_2': 114}
            rgb_list.append('{} {} {}\n'.format(frame_dir, rgb_cnt, item[1]))
            flow_list.append('{} {} {}\n'.format(frame_dir, flow_cnt, item[1]))
            if item[0] == '10-r_0':
                print('+++++++++++++++++++++++++++++++++++++++,', item, frame_dir, rgb_cnt, flow_cnt)
        if shuffle:
            random.shuffle(rgb_list)
            random.shuffle(flow_list)
        return rgb_list, flow_list

    train_rgb_list, train_flow_list = build_set_list(split[0])
    test_rgb_list, test_flow_list = build_set_list(split[1])
    return (train_rgb_list, test_rgb_list), (train_flow_list, test_flow_list)


## Dataset specific split file parse
def parse_ucf_splits():
    class_ind = [x.strip().split() for x in open('data/ucf101_splits/classInd.txt')]
    class_mapping = {x[1]:int(x[0])-1 for x in class_ind}

    def line2rec(line):
        items = line.strip().split('/')
        label = class_mapping[items[0]]
        vid = items[1].split('.')[0]
        return vid, label

    splits = []
    for i in xrange(1, 4):
        train_list = [line2rec(x) for x in open('data/ucf101_splits/trainlist{:02d}.txt'.format(i))]
        test_list = [line2rec(x) for x in open('data/ucf101_splits/testlist{:02d}.txt'.format(i))]
        splits.append((train_list, test_list))
    return splits


def parse_hmdb51_splits():
    # load split file
    class_files = glob.glob('data/hmdb51_splits/*split*.txt')
    open('/home/LX/class_file.txt', 'w').writelines(str(class_file))

    # load class list
    class_list = [x.strip() for x in open('data/hmdb51_splits/class_list.txt')]
    class_dict = {x: i for i, x in enumerate(class_list)}
    print(class_dict)

    def parse_class_file(filename):
        # parse filename parts
        filename_parts = filename.split('/')[-1][:-4].split('_')
        split_id = int(filename_parts[-1][-1])
        class_name = '_'.join(filename_parts[:-2])

        # parse class file contents
        contents = [x.strip().split() for x in open(filename).readlines()]
        train_videos = [ln[0][:-4] for ln in contents if ln[1] == '1']
        test_videos = [ln[0][:-4] for ln in contents if ln[1] == '2']

        return class_name, split_id, train_videos, test_videos

    class_info_list = map(parse_class_file, class_files)

    splits = []
    for i in xrange(1, 4):
        train_list = [
            (vid, class_dict[cls[0]]) for cls in class_info_list for vid in cls[2] if cls[1] == i
        ]
        test_list = [
            (vid, class_dict[cls[0]]) for cls in class_info_list for vid in cls[3] if cls[1] == i
        ]
        splits.append((train_list, test_list))
    return splits


def parse_activitynet_splits(version):
    db = ANetDB.get_db(version)
    train_instance = db.get_subset_instance('training')
    val_instance = db.get_subset_instance('validation')
    test_instance = db.get_subset_videos('testing')

    splits = []

    train_list = [(x.name, x.num_label) for x in train_instance]
    val_list = [(x.name, x.num_label) for x in val_instance]
    test_list = [(x.id, 0) for x in test_instance]

    splits.append((train_list, val_list))
    splits.append((train_list + val_list, test_list))

    return splits