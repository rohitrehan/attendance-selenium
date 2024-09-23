pushd src
call ruff --fix --exclude test .
popd
pushd salesdemo-data
call ruff --fix --exclude test .
popd