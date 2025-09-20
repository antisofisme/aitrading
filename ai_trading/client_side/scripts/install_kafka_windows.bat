@echo off
echo ===========================================
echo Installing Kafka Libraries for MT5 Bridge
echo ===========================================

echo Installing aiokafka...
pip install aiokafka

echo Installing kafka-python...
pip install kafka-python

echo Installing async-timeout...
pip install async-timeout

echo ===========================================
echo Testing installation...
echo ===========================================

python -c "import aiokafka; print('✅ aiokafka installed successfully')" 2>nul || echo "❌ aiokafka installation failed"
python -c "import kafka; print('✅ kafka-python installed successfully')" 2>nul || echo "❌ kafka-python installation failed"

echo ===========================================
echo Installation completed!
echo You can now restart the MT5 Bridge.
echo ===========================================

pause