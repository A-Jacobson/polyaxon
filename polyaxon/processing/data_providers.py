# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import numpy as np
import tensorflow as tf

from tensorflow.contrib.slim.python.slim.data.data_provider import DataProvider
from tensorflow.contrib.slim.python.slim.data.parallel_reader import parallel_read

from polyaxon.processing.data_decoders import SplitTokensDecoder


def make_parallel_data_provider(data_sources_source,
                                data_sources_target,
                                reader=tf.TextLineReader,
                                num_samples=None,
                                decoder_source=None,
                                decoder_target=None,
                                **kwargs):
    """Creates a DataProvider that reads parallel text data.

        Args:
            data_sources_source: A list of data sources for the source text files.
            data_sources_target: A list of data sources for the target text files.
              Can be None for inference mode.
            num_samples: Optional, number of records in the dataset
            delimiter: Split tokens in the data on this delimiter. Defaults to space.
            decoder_source: an instance of DataDecoder
            e.g.:
            ```python
            >>> decoder_source = SplitTokensDecoder(
            >>>     tokens_feature_name="source_tokens",
            >>>     length_feature_name="source_len",
            >>>     append_token="SEQUENCE_END",
            >>>     delimiter=" ")
            ```
            decoder_target: an instance of DataDecoder
            e.g.:
            ```python
            >>> decoder_target = SplitTokensDecoder(
            >>>     tokens_feature_name="target_tokens",
            >>>     length_feature_name="target_len",
            >>>     prepend_token="SEQUENCE_START",
            >>>     append_token="SEQUENCE_END",
            >>>     delimiter=target_delimiter)
            ```
            kwargs: Additional arguments (shuffle, num_epochs, etc) that are passed
              to the data provider

        Returns:
            A DataProvider instance
    """
    dataset_source = tf.contrib.slim.dataset.Dataset(
        data_sources=data_sources_source,
        reader=reader,
        decoder=decoder_source,
        num_samples=num_samples,
        items_to_descriptions={})

    dataset_target = None
    if data_sources_target is not None:
        dataset_target = tf.contrib.slim.dataset.Dataset(
            data_sources=data_sources_target,
            reader=reader,
            decoder=decoder_target,
            num_samples=num_samples,
            items_to_descriptions={})

    return ParallelDataProvider(
        dataset_source=dataset_source, dataset_target=dataset_target, **kwargs)


class ParallelDataProvider(DataProvider):
    """Creates a ParallelDataProvider. This data provider reads two datasets
    in parallel, keeping them aligned.

        Args:
            dataset1: The first dataset. An instance of the Dataset class.
            dataset2: The second dataset. An instance of the Dataset class.
                Can be None. If None, only `dataset1` is read.
            num_readers: The number of parallel readers to use.
            shuffle: Whether to shuffle the data sources and common queue when
              reading.
            num_epochs: The number of times each data source is read. If left as None,
              the data will be cycled through indefinitely.
            common_queue_capacity: The capacity of the common queue.
            common_queue_min: The minimum number of elements in the common queue after
              a dequeue.
            seed: The seed to use if shuffling.
      """

    def __init__(self,
                 dataset_source,
                 dataset_target,
                 shuffle=True,
                 num_epochs=None,
                 common_queue_capacity=4096,
                 common_queue_min=1024,
                 seed=None):

        if seed is None:
            seed = np.random.randint(10e8)

        _, data_source = parallel_read(
            dataset_source.data_sources,
            reader_class=dataset_source.reader,
            num_epochs=num_epochs,
            num_readers=1,
            shuffle=False,
            capacity=common_queue_capacity,
            min_after_dequeue=common_queue_min,
            seed=seed)

        data_target = ""
        if dataset_target is not None:
            _, data_target = parallel_read(
                dataset_target.data_sources,
                reader_class=dataset_target.reader,
                num_epochs=num_epochs,
                num_readers=1,
                shuffle=False,
                capacity=common_queue_capacity,
                min_after_dequeue=common_queue_min,
                seed=seed)

        # Optionally shuffle the data
        if shuffle:
            shuffle_queue = tf.RandomShuffleQueue(
                capacity=common_queue_capacity,
                min_after_dequeue=common_queue_min,
                dtypes=[tf.string, tf.string],
                seed=seed)
            enqueue_ops = []
            enqueue_ops.append(shuffle_queue.enqueue([data_source, data_target]))
            tf.train.add_queue_runner(
                tf.train.QueueRunner(shuffle_queue, enqueue_ops))
            data_source, data_target = shuffle_queue.dequeue()

        # Decode source items
        items = dataset_source.decoder.list_items()
        tensors = dataset_source.decoder.decode(data_source, items)

        if dataset_target is not None:
            # Decode target items
            items2 = dataset_target.decoder.list_items()
            tensors2 = dataset_target.decoder.decode(data_target, items2)

            # Merge items and results
            items = items + items2
            tensors = tensors + tensors2

        super(ParallelDataProvider, self).__init__(
            items_to_tensors=dict(zip(items, tensors)),
            num_samples=dataset_source.num_samples)
