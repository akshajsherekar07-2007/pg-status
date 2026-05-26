/**
 * StaySync — Upload
 * Drag-drop AJAX upload with previews
 */

function initUploadZone(zoneId, entityType, entityId) {
    const zone = document.getElementById(zoneId);
    if (!zone) return;

    zone.addEventListener('dragover', (e) => {
        e.preventDefault();
        zone.classList.add('dragover');
    });

    zone.addEventListener('dragleave', () => {
        zone.classList.remove('dragover');
    });

    zone.addEventListener('drop', (e) => {
        e.preventDefault();
        zone.classList.remove('dragover');
        const files = e.dataTransfer.files;
        for (const file of files) uploadFile(file, entityType, entityId, zoneId);
    });

    zone.addEventListener('click', () => {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.jpg,.jpeg,.png,.webp';
        input.multiple = true;
        input.onchange = () => {
            for (const file of input.files) uploadFile(file, entityType, entityId, zoneId);
        };
        input.click();
    });
}

async function uploadFile(file, entityType, entityId, zoneId) {
    if (file.size > 5 * 1024 * 1024) {
        showToast('error', 'File Too Large', 'Maximum file size is 5MB.');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
        const res = await fetch(`/api/upload/${entityType}/${entityId}`, {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        if (data.success) {
            showToast('success', 'Upload Complete', 'Photo uploaded successfully.');
            addPreview(data.data.file_path, data.data.media_id, zoneId);
        } else {
            showToast('error', 'Upload Failed', data.error);
        }
    } catch (e) {
        showToast('error', 'Upload Error', 'Failed to upload file.');
    }
}

function addPreview(filePath, mediaId, zoneId) {
    const previewGrid = document.getElementById(zoneId + '-previews');
    if (!previewGrid) return;

    const item = document.createElement('div');
    item.className = 'upload-preview-item';
    item.innerHTML = `
        <img src="/static/${filePath}" alt="Upload" loading="lazy">
        <div class="upload-preview-delete" onclick="deleteMedia(${mediaId}, this.parentElement)">✕</div>
    `;
    previewGrid.appendChild(item);
}

async function deleteMedia(mediaId, element) {
    try {
        const res = await fetch(`/api/media/${mediaId}`, { method: 'DELETE' });
        const data = await res.json();
        if (data.success) {
            element.remove();
            showToast('success', 'Deleted', 'Photo removed.');
        }
    } catch (e) {
        showToast('error', 'Error', 'Failed to delete photo.');
    }
}
