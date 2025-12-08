"""
查询客户端状态示例

演示如何使用SharedState查询Handler服务中客户端是否正在说话
"""
import os
import sys
from loguru import logger

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.shared_state import SharedState


def query_client_status(client_id: str = None):
    """
    查询客户端是否正在说话
    
    Args:
        client_id: 客户端ID，如果为None则查询所有客户端
    
    Returns:
        dict: 查询结果
    """
    try:
        if client_id:
            # 查询指定客户端
            status = SharedState.get(f"client_status:{client_id}")
            if status:
                result = {
                    'success': True,
                    'client_id': client_id,
                    'is_speaking': status.get('is_speaking', False),
                    'session_id': status.get('session_id'),
                    'last_update': status.get('last_update')
                }
            else:
                result = {
                    'success': False,
                    'error': f'Client {client_id} not found'
                }
        else:
            # 查询所有客户端
            all_clients = SharedState.get("client_list", [])
            clients_status = {}
            for cid in all_clients:
                status = SharedState.get(f"client_status:{cid}")
                if status:
                    clients_status[cid] = {
                        'is_speaking': status.get('is_speaking', False),
                        'session_id': status.get('session_id'),
                        'last_update': status.get('last_update')
                    }
            
            result = {
                'success': True,
                'clients': clients_status
            }
        
        logger.info(f"查询结果: {result}")
        return result
        
    except Exception as e:
        logger.error(f"查询失败: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def list_clients():
    """列出所有连接的客户端"""
    try:
        all_clients = SharedState.get("client_list", [])
        result = {
            'success': True,
            'clients': all_clients
        }
        logger.info(f"客户端列表: {result}")
        return result
        
    except Exception as e:
        logger.error(f"查询失败: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='查询客户端状态')
    parser.add_argument('--action', choices=['is_speaking', 'list_clients'], 
                       default='is_speaking', help='查询动作')
    parser.add_argument('--client-id', type=str, default=None, 
                       help='客户端ID（仅用于is_speaking动作）')
    
    args = parser.parse_args()
    
    if args.action == 'is_speaking':
        query_client_status(args.client_id)
    elif args.action == 'list_clients':
        list_clients()


if __name__ == "__main__":
    main()

