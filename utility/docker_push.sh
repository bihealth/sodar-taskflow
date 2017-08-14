#!/usr/bin/env bash
cd ..
docker build -t cubi-gitlab.bihealth.org:4567/cubi_engineering/cubi_data_mgmt/omics_taskflow .
docker push cubi-gitlab.bihealth.org:4567/cubi_engineering/cubi_data_mgmt/omics_taskflow

