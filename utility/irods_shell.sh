#!/usr/bin/env bash
echo "Opening shell on omics_irods as user irods"
docker exec -it -u irods omics_irods /bin/bash
