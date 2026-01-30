# Copyright (c) 2023 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
FROM debian:bullseye

RUN apt-get update && \
    apt-get install -y \
        mmdebstrap \
        debos \
        ostree \
        python3 \
        python3-apt \
        python3-click \
        python3-pip \
        python3-pbr \
        python3-rich \
        gir1.2-ostree-1.0 \
        dosfstools \
        rsync \
        xfsprogs \
        python3-gi \
        python3-yaml \
        python3-systemd \
        dosfstools \
        reprepro

ADD assets/pip.conf /etc/pip.conf

RUN mkdir -p /usr/src/apt-ostree
WORKDIR /usr/src/apt-ostree
