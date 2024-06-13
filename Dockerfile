FROM python:3.8-slim

WORKDIR /home

RUN apt-get update && apt-get install -y wget tar libx11-dev libxpm-dev libxft-dev libxext-dev

# Download and install ROOT
RUN wget https://root.cern/download/root_v6.30.06.Linux-almalinux9.3-x86_64-gcc11.4.tar.gz && \
    tar -xzvf root_v6.30.06.Linux-almalinux9.3-x86_64-gcc11.4.tar.gz && \
    rm root_v6.30.06.Linux-almalinux9.3-x86_64-gcc11.4.tar.gz

ENV ROOTSYS /home/root
ENV PATH $ROOTSYS/bin:$PATH
ENV LD_LIBRARY_PATH $ROOTSYS/lib:$LD_LIBRARY_PATH
ENV PYTHONPATH $ROOTSYS/lib:$PYTHONPATH

COPY include/root/requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY include/root/script.py script.py
COPY include/root/db_config.ini db_config.ini

# ENTRYPOINT ["python", "script.py"]
