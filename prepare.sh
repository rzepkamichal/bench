#!/bin/bash

#git pull

working_dir="$(pwd)"
source_path="$1"
workload_src="workload-generator"
experiment_runner_src="$source_path/experiment-runner/src"
experiment_spec_src="$source_path/experiments"

rm -rf workload-generator.jar experiment-runner experiments

cd "$source_path" || exit 1
echo "Source Directory:" $(pwd)

cd "$workload_src"
mvn clean && mvn package
cp target/bookkeeper-workload-generator-1.0.jar "$working_dir"
cd "$working_dir"
mv bookkeeper-workload-generator-1.0.jar workload-generator.jar

cp -r "$experiment_runner_src" "$working_dir/experiment-runner"

cp -r "$experiment_spec_src" "$working_dir"

if [ -d "$working_dir/experiments/archived" ]; then
    rm -rf "$working_dir/experiments/archived"
fi

if [ -d "$working_dir/experiment-runner/env" ]; then
    rm -rf "$working_dir/experiments/env"
fi

git add *
git commit -m 'new version'
