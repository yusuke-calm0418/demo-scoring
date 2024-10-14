document.addEventListener('DOMContentLoaded', function () {
        const editModal = document.getElementById('editModal');
        const deleteModal = document.getElementById('deleteModal');
        const deleteForm = document.getElementById('deleteForm');

        // 編集ボタンをクリックしたときの処理
        document.querySelectorAll('.edit-button').forEach(button => {
            button.addEventListener('click', function () {
                const statusId = this.dataset.statusId;
                const statusName = this.dataset.statusName;
                const color = this.dataset.color;
                const memo = this.dataset.memo;

                document.getElementById('edit_status_name').value = statusName;
                document.getElementById('edit_color').value = color;
                document.getElementById('edit_memo').value = memo;

                document.getElementById('editForm').action = `/score/edit_status/${statusId}/`;

                editModal.classList.remove('hidden');
            });
        });

        // 削除ボタンをクリックしたときの処理
        document.querySelectorAll('.delete-button').forEach(button => {
            button.addEventListener('click', function () {
                const statusId = this.dataset.statusId;
                deleteForm.action = `/score/delete_status/${statusId}/`;
                deleteModal.classList.remove('hidden');
            });
        });

        // 編集モーダルのキャンセルボタン
        document.getElementById('cancelEdit').addEventListener('click', function () {
            editModal.classList.add('hidden');
        });

        // 削除モーダルのキャンセルボタン
        document.getElementById('cancelDelete').addEventListener('click', function () {
            deleteModal.classList.add('hidden');
        });
    });
