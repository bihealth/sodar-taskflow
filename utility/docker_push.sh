#!/usr/bin/env bash
cd ..
docker login gitlab.bihealth.org:4567
docker build -t gitlab.bihealth.org:4567/cubi_data_mgmt/omics_taskflow/omics_taskflow .
docker push gitlab.bihealth.org:4567/cubi_data_mgmt/omics_taskflow/omics_taskflow
