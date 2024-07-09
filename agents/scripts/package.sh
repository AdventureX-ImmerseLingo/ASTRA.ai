#!/usr/bin/env bash

APP_HOME=$(cd $(dirname $0)/..; pwd)

cd $APP_HOME

rm -rf .release
mkdir .release

copy_extension() {
  local extension=$1
  mkdir -p .release/addon/extension/$extension

  if [[ -d addon/extension/$extension/lib ]]; then
    cp -r addon/extension/$extension/lib .release/addon/extension/$extension/
  fi

  if [[ -f addon/extension/$extension/manifest.json ]]; then
    cp addon/extension/$extension/manifest.json .release/addon/extension/$extension/

    # package .py for python extensions 
    EXTENSION_LANGUAGE=$(jq -r '.language' addon/extension/$extension/manifest.json)
    if [[ $EXTENSION_LANGUAGE == "python" ]]; then
      # TODO: package 'publish' contents only
      cp addon/extension/$extension/*.py .release/addon/extension/$extension/
    fi
  fi

  if [[ -f addon/extension/$extension/property.json ]]; then
    cp addon/extension/$extension/property.json .release/addon/extension/$extension/
  fi
}

cp -r bin .release
cp -r lib .release
cp manifest.json .release
cp manifest.elevenlabs.json .release
cp property.json .release

# python main and deps
if [[ -f main.py ]]; then
  cp main.py .release
fi
if [[ -d interface/rte_runtime_python ]]; then
  mkdir -p .release/interface
  cp -r interface/rte_runtime_python .release/interface
fi

# extension group
mkdir -p .release/addon
cp -r addon/extension_group .release/addon/

# extensions
mkdir -p .release/addon/extension
for extension in addon/extension/*
do
  extension_name=$(basename $extension)
  copy_extension $extension_name
done

if [[ -f session_control.conf ]]; then
  cp -r session_control.conf .release/
fi
