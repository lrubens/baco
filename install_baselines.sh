mkdir extra_packages
cd extra_packages

git clone https://github.com/ytopt-team/ConfigSpace.git --depth=1
cd ConfigSpace
pip install -e .
cd ..

git clone https://github.com/ytopt-team/scikit-optimize.git --depth=1
cd scikit-optimize
pip install -e .
cd ..

git clone -b version1 https://github.com/ytopt-team/autotune.git --depth=1
cd autotune
pip install -e . 
cd ..

git clone -b main https://github.com/ytopt-team/ytopt.git --depth=1
cd ytopt
pip install -e .
cd ..

sudo apt-get install autoconf automake libtool libgsl-dev
git clone https://github.com/argonne-lcf/CCS.git
cd CCS
./autogen.sh
mkdir build
cd build
../configure
make
make install
cd ../bindings/python
pip install parglare==0.12.0
pip install -e .

cd ../../..

pip install opentuner
sed -i "s@np.int)@np.int64)@g" scikit-optimize/skopt/space/transformers.py
