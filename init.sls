# Install python36 and requirements
ius-release:
  pkg.installed:
  - sources:
    - ius-release: https://centos7.iuscommunity.org/ius-release.rpm

python36u-pip:
  pkg.installed: []

# Install gatling_exporter
/etc/gatling_exporter/gatling_exporter.py:
  file.managed:
    - source: salt://prometheus/gatling_exporter/gatling_exporter.py
    - makedirs: True
    - user: admin
    - group: admin
    - mode: 644

gatling_exporter_requirements:
  pip.installed:
  - bin_env: '/usr/bin/pip3.6'
  - requirements: salt://prometheus/gatling_exporter/requirements.txt

# To run the exporter add the following script to your sls
#
# {% set EXPORTER_VERSION='0.1.0' %}
# If exporter is running kill it first. Before redeploy
# For some reason pkill is returning -15 even if successful on salt
#kill_gatling_exporter:
#  cmd.run:
#  - name: |
#      pkill -f /etc/gatling_exporter/gatling_exporter.py || true
#  - check_cmd: # workaround
#    - /bin/true
#  - runas: admin
#  - unless: "curl localhost:9102 > /dev/null && python3.6 /etc/gatling_exporter/gatling_exporter.py -v | grep {{ EXPORTER_VERSION }}"
#
#run_gatling_exporter:
#  cmd.run:
#  - name: |
#      python3.6 /etc/gatling_exporter/gatling_exporter.py \
#      -s path_to_gatling_simulation_log_file
#  - runas: admin
#  - bg: True
#  - unless: "curl localhost:9102 > /dev/null && python3.6 /etc/gatling_exporter/gatling_exporter.py -v | grep {{ EXPORTER_VERSION }}"
