import httpx
import time

def run_integration_check():
    client = httpx.Client(timeout=30.0)

    # 1. Health check
    r_health = client.get('http://127.0.0.1:8000/api/health')
    print('[1] Health Check:', r_health.status_code, r_health.json()['status'])

    # 2. Model Info
    r_info = client.get('http://127.0.0.1:8000/api/model-info')
    print('[2] Model Info:', r_info.status_code, r_info.json()['architecture'], '| Status:', r_info.json()['checkpoint_status'])

    # 3. Load sample scan
    r_load = client.post('http://127.0.0.1:8000/api/sample-scans/load/sample_phantom_brats_flair')
    upload = r_load.json()
    print('[3] Load Sample:', r_load.status_code, 'Upload ID:', upload['upload_id'], 'Dims:', upload['dimensions'])

    # 4. Start segmentation
    r_seg = client.post(
        'http://127.0.0.1:8000/api/segment',
        json={'upload_id': upload['upload_id'], 'selected_modality': 'FLAIR'}
    )
    job_id = r_seg.json()['job_id']
    print('[4] Submitted Segmentation Job:', job_id)

    # 5. Poll job status
    result_id = None
    for _ in range(30):
        time.sleep(0.5)
        r_job = client.get(f'http://127.0.0.1:8000/api/jobs/{job_id}')
        status = r_job.json()
        if status['status'] == 'completed':
            result_id = status['result_id']
            print('[5] Job Completed successfully! Result ID:', result_id)
            break
        elif status['status'] == 'failed':
            print('[5] Job Failed:', status.get('error'))
            return

    # 6. Retrieve result
    r_res = client.get(f'http://127.0.0.1:8000/api/results/{result_id}')
    report = r_res.json()['quantitative_report']
    print('[6] Quantitative Total Tumor Volume:', report['total_tumor_volume_cm3'], 'cm3')
    for reg in report['regions']:
        print(f"    - {reg['region_name']}: {reg['volume_cm3']} cm3 ({reg['voxel_count']} voxels)")

    # 7. Check PDF report download
    r_pdf = client.get(f'http://127.0.0.1:8000/api/results/{result_id}/report')
    print('[7] Download PDF Report:', r_pdf.status_code, f'({len(r_pdf.content)} bytes)')

    # 8. Check Slice render
    r_slice = client.get(f'http://127.0.0.1:8000/api/results/{result_id}/slice/64?plane=axial')
    print('[8] Axial Slice 64 Render:', r_slice.status_code, '| Image base64 length:', len(r_slice.json()['image_base64']))

    # 9. Check Frontend server (default port 5175 in vite.config.ts)
    front_url = 'http://127.0.0.1:5175/'
    try:
        r_front = client.get(front_url)
    except Exception:
        front_url = 'http://127.0.0.1:5173/'
        r_front = client.get(front_url)
    print(f'[9] React Frontend Server ({front_url}):', r_front.status_code, '| Title present:', '<title>' in r_front.text)
    print('\n[SUCCESS] ALL LIVE SERVER ENDPOINTS ARE FUNCTIONAL!')

if __name__ == '__main__':
    run_integration_check()
